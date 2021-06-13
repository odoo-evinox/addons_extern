from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from _ast import Or
from distlib.util import OR



class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    original_description = fields.Text(readonly=1,help="Original text imported from bank statement")
    separated_description = fields.Text(readonly=1,help="Original text separated by ; and replace by line feed; exist also the original_descriptin field")
    bank_tranzaction_uniqueid = fields.Char(readonly=1,help="if this is not null is the ank unique tranzaction id and must be unique")

    bank_balance = fields.Float(readonly=1,help="the balance from imported bank statement")

    sequence = fields.Integer(readonly=1,index=True, help="Gives the sequence order when displaying a list of bank statement lines.", default=1)
    is_bank_fee = fields.Boolean()
    is_bank_interest = fields.Boolean()

    transfer_journal_id = fields.Many2one('account.journal', domain=[('type','in',['bank','cash'])],help="current transfer is connected with this they must have the same amount and same state", tracking =1)
    transfer_related_payment_id = fields.Many2one('account.payment',readonly=1,tracking=1)

# just tracking
    amount = fields.Monetary(tracking=1)
    payment_type = fields.Selection(tracking=1)
    parnter_id = fields.Many2one('res.partner',tracking=1)

    @api.constrains('is_internal_transfer','is_bank_fee','is_bank_interest','transfer_journal_id','journal_id','transfer_related_payment_id')
    def constrains_is(self):
        for rec in self:
            nr_of_is = 0
            if rec.is_internal_transfer: 
                nr_of_is += 1
            if rec.is_bank_fee: nr_of_is += 1
            if rec.is_bank_interest: nr_of_is += 1
            if nr_of_is>=2:
                raise ValidationError(f'In account payment {rec.id} we can have maximm one of is_internal_transfer, is tank_fee or is_tank_interest. here =({rec.is_internal_transfer},{rec.is_bank_fee} ,{rec.is_bank_interest} ) ')
            if rec.is_internal_transfer: 
                if not rec.transfer_journal_id or not rec.journal_id or (rec.transfer_journal_id == rec.journal_id):
                    raise ValidationError(f"at res={rec} that is transfer you must have jounrnal_id and transfer_journal_id not null and different")
                if rec.transfer_related_payment_id:
                    if rec.amount != rec.transfer_related_payment_id.amount or rec.date != rec.transfer_related_payment_id.date or rec.journal_id != rec.transfer_related_payment_id.transfer_journal_id or rec.transfer_journal_id != rec.transfer_related_payment_id.journal_id or  rec.transfer_related_payment_id.payment_type == rec.payment_type:
                        raise ValidationError(f"at res={rec} that is transfer you have a inverse transfer {rec.transfer_related_payment_id}   you must have the same date amount and iverse journals but is not the case")

    @api.model
    def create(self,values,):
        rec = super().create(values)
        is_internal_transfer = values.get('is_internal_transfer')
        if is_internal_transfer:
            values2=values.copy()
            values2.update({'payment_type':'outbound' if values.get('payment_type')=='inbound' else 'inbound',
                            'partner_type':'customer' if values.get('partner_type')=='supplier' else 'supplier',
                            'journal_id':values.get('transfer_journal_id',False),
                            'transfer_journal_id':values.get('journal_id',False),
                            'ref':f"REVERS OF {rec}; " + (values.get('ref') or ''),
                            'name':'/',
                            'partner_bank_id':False,
                            'move_id':False,
                            'bank_tranzaction_uniqueid':'',
                            'transfer_related_payment_id':rec.id,
                            'bank_balance':0,
            
                })
            rec2 = super().create(values2)  #without super is a loop
            rec.write({"transfer_related_payment_id":rec2.id, 'ref': f"REVERS OF {rec2}" + values2['ref'].split(';',1)[1]})
        return rec
        
    def write(self,values):
        is_internal_transfer = values.get('is_internal_transfer')
        if not is_internal_transfer:
            internal_transfers = self.filtered(lambda r: r.is_internal_transfer)
            if internal_transfers:
                keys = values.keys()
                if 'date' in keys or 'payment_type' in keys  or 'amount' in keys or 'journal_id' in keys or 'transfer_journal_id' in keys:
                    raise ValidationError("You can't modify ( write) a transfer because it has another transfer related on it. Simpler delete it and create it again",)
                
        return super().write(values)
    
    def unlink(self):
        for rec in self:
            if rec.is_internal_transfer and rec.transfer_related_payment_id:
                if rec.transfer_related_payment_id not in self:
                    super(AccountPayment,rec.transfer_related_payment_id).unlink()
        return super().unlink()

    def action_post(self):
        ''' draft -> posted '''
        self.move_id._post(soft=False)  # till here was the original behavior
        transfer_related_payment_id = self.filtered(lambda r:r.transfer_related_payment_id )
        if transfer_related_payment_id:
            transfer_related_payment_id.move_id._post(soft=False)        

    def action_cancel(self):
        ''' draft -> cancelled '''
        self.move_id.button_cancel()
        transfer_related_payment_id = self.filtered(lambda r:r.transfer_related_payment_id )
        if transfer_related_payment_id:
            transfer_related_payment_id.move_id.button_cancel()        
    
    def action_draft(self):
        ''' posted -> draft '''
        self.move_id.button_draft()
        transfer_related_payment_id = self.filtered(lambda r:r.transfer_related_payment_id )
        if transfer_related_payment_id:
            transfer_related_payment_id.move_id.action_draft()        

    @api.depends('is_internal_transfer','is_bank_fee','is_bank_interest')
    def _compute_partner_id(self):  # overwrite original function that has only is_internal_transfer
        for pay in self:
            if pay.is_internal_transfer or pay.is_bank_fee or pay.is_bank_interest:
                pay.partner_id = pay.journal_id.company_id.partner_id
            elif pay.partner_id == pay.journal_id.company_id.partner_id:
                pay.partner_id = False
            else:
                pay.partner_id = pay.partner_id

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        if not self.journal_id.payment_debit_account_id or not self.journal_id.payment_credit_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set on the %s journal.",
                self.journal_id.display_name))

        # Compute amounts.
        write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
            write_off_amount_currency *= -1
        else:
            liquidity_amount_currency = write_off_amount_currency = 0.0

        write_off_balance = self.currency_id._convert(
            write_off_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        liquidity_balance = self.currency_id._convert(
            liquidity_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id

        if self.is_internal_transfer:
            if self.payment_type == 'inbound':
                liquidity_line_name = _('Transfer to %s', self.journal_id.name)
            else: # payment.payment_type == 'outbound':
                liquidity_line_name = _('Transfer from %s', self.journal_id.name)
        else:
            liquidity_line_name = self.payment_reference

        # Compute a default label to set on the journal items.

        payment_display_name = {
            'outbound-customer': _("Customer Reimbursement"),
            'inbound-customer': _("Customer Payment"),
            'outbound-supplier': _("Vendor Payment"),
            'inbound-supplier': _("Vendor Reimbursement"),
        }

        default_line_name = self.env['account.move.line']._get_default_line_name(
            _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )

        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name or default_line_name,
                'date_maturity': self.date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': currency_id,
                'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.journal_id.payment_credit_account_id.id if liquidity_balance < 0.0 else self.journal_id.payment_debit_account_id.id,
            },
            # Receivable / Payable.
            {
                'name': self.payment_reference or default_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            },
        ]
        if not self.currency_id.is_zero(write_off_amount_currency):
            # Write-off line.
            line_vals_list.append({
                'name': write_off_line_vals.get('name') or default_line_name,
                'amount_currency': write_off_amount_currency,
                'currency_id': currency_id,
                'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': write_off_line_vals.get('account_id'),
            })
        return line_vals_list

                

    @api.constrains('bank_tranzaction_uniqueid')
    def constrains_bank_tranzaction_uniqueid(self):
        for rec in self:
            if rec.bank_tranzaction_uniqueid:
                same_id = self.search([('rec.bank_tranzaction_uniqueid','=',rec.bank_tranzaction_uniqueid),('id','not in', rec.ids)],limit=1)
                if same_id:
                    raise ValidationError(f'we have same bank_tranzaction_uniqueid={rec.bank_tranzaction_uniqueid} in {same_id}')

