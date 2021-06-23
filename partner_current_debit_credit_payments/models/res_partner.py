from odoo import fields, models, api
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"

    payment_ids = fields.One2many('account.payment', 'partner_id', string='Payments', readonly=True, copy=False)
    total_payments = fields.Monetary(compute='_payment_total', string="Total Payment",
        groups='account.group_account_invoice,account.group_account_readonly')
    total_bills = fields.Monetary(compute='_bills_total', string="Total Bills",
        groups='account.group_account_invoice,account.group_account_readonly')

    credit_all_children = fields.Monetary(compute='_credit_debit_all_children', string='Total Receivable on all children', help="Total amount this customer owes you on all companies contacts under it (only first child).")
    debit_all_children = fields.Monetary(compute='_credit_debit_all_children', string='Total Payable on all children', help="Total amount this customer owes you on all companies contacts under it (only first child).")

# just add tracking on this field defined in base
    credit_limit = fields.Float(tracking=1)

# this is to check over the limit
    def return_parent_or_self(self):
        self.ensure_one()
        if self.parent_id:
            return self.parent_id.return_parent_or_self()
        else:
            return self
        
    def check_over_credit_limit(self,with_this_sum=0):
        self.ensure_one()
        parent_or_self = self.return_parent_or_self()
        if parent_or_self.credit_limit >0 and with_this_sum>0:
            credit_all_children = parent_or_self.credit_all_children
            debit_all_children = parent_or_self.debit_all_children
            future_credit = with_this_sum + credit_all_children - debit_all_children
            if parent_or_self.credit_limit < future_credit:
                    raise ValidationError(f"You can not validate this sale order/invoice because the partner={parent_or_self.name} has a credit limit of {parent_or_self.credit_limit:.2f}; credit_all_children={credit_all_children:.2f}, debit_on_all_children={debit_all_children:.2f} and with this invoice/sale_order is going to have {future_credit:.2f} (without transport taxes)")
#/this is to check over the limit

    @api.depends_context('company')
    def _credit_debit_all_children(self):
        tables, where_clause, where_params = self.env['account.move.line'].with_context(state='posted', company_id=self.env.company.id)._query_get()

        all_partners_and_children = {}
        all_partner_ids = []
        all_partners_and_children_values ={}
        child_to_partner = {}
        for partner in self.filtered('id'):
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            for child in all_partners_and_children[partner]:
                child_to_partner[child] = partner
            all_partner_ids += all_partners_and_children[partner]       
            all_partners_and_children_values[partner] = {'debit':0,'credit':0}

        where_params = [tuple(all_partner_ids)] + where_params

        if where_clause:
            where_clause = 'AND ' + where_clause
        self._cr.execute("""SELECT account_move_line.partner_id, act.type, SUM(account_move_line.amount_residual)
                      FROM """ + tables + """
                      LEFT JOIN account_account a ON (account_move_line.account_id=a.id)
                      LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                      WHERE act.type IN ('receivable','payable')
                      AND account_move_line.partner_id IN %s
                      AND account_move_line.reconciled IS NOT TRUE
                      """ + where_clause + """
                      GROUP BY account_move_line.partner_id, act.type
                      """, where_params)
        for pid, type, val in self._cr.fetchall():
            if type == 'receivable':
                all_partners_and_children_values[child_to_partner[pid]]['credit']+=val
            elif type == 'payable':
                all_partners_and_children_values[child_to_partner[pid]]['debit']-=val
        for partner in all_partners_and_children_values:
            partner.credit_all_children =  all_partners_and_children_values[partner]['credit']
            partner.debit_all_children =  all_partners_and_children_values[partner]['debit']
            
            


    def _payment_total(self):
        self.total_payments = 0
        if not self.ids:
            return True

        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self.filtered('id'):
            # price_total is in the company currency
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]

        domain = [
            ('partner_id', 'in', all_partner_ids),
            ('state', 'not in', ['draft', 'cancel']),        ]
        totals = self.env['account.payment'].read_group(domain, ['amount'], ['payment_type'])
        for partner, child_ids in all_partners_and_children.items():
            partner.total_payments = sum(x['amount']*(1 if x['amount']=='inbound' else (-1)) for x in totals )

    def action_view_partner_payments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments")
        action['domain'] = [
           # ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('partner_id', 'child_of', self.id),
        ]
        action['context'] = {}
        return action    

    def _bills_total(self):
        self.total_bills = 0
        if not self.ids:
            return True

        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self.filtered('id'):
            # price_total is in the company currency
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]

        domain = [
            ('partner_id', 'in', all_partner_ids),
            ('state', 'not in', ['draft', 'cancel']),
            ('move_type', 'in', ('in_invoice', 'in_refund')),
        ]
        price_totals = self.env['account.invoice.report'].search(domain)  
        for partner, child_ids in all_partners_and_children.items():
            partner.total_bills = sum(x.move_id.amount_total for x in price_totals)
