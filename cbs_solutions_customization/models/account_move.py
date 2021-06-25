from odoo import models, fields, api, _
import json

class AccountMove(models.Model):
    _inherit = ["account.move"]
    _name = "account.move"

    # sale_order_ids = fields.Many2many("sale.order", compute="compute_sale_orders", string='Sale Orders', store=True)
    # sale_order_ids_name = fields.Char(compute="compute_sale_orders", string='From Sales', )
    #
    # @api.depends('invoice_line_ids')
    # def compute_sale_orders(self):
        # for rec in self:
            # sale_order_ids = self.env['sale.order'] 
            # sale_order_ids_name = ''
            # for  line in rec.invoice_line_ids:
                # for x in line.sale_line_ids:
                    # sale_order_ids |= x.order_id
            # rec.sale_order_ids = sale_order_ids
            # if sale_order_ids:
                # sale_order_ids_name = ', '.join([x.name for x in sale_order_ids])
            # rec.sale_order_ids_name = sale_order_ids_name

    invoice_payment_ids = fields.Many2many("account.payment",string="Invoice account.payment", compute="_compute_invoice_payment_ids", help="the payments for this invoice (from account.payment (if a line form accont_payment has some sum matched with a line from this invoice)). The invoice can be paid also with another invoice (credit note) or with another type of accounting entry - you are not going to see this here. This is used to print the invoice with cache payments  ")
    
    def _compute_invoice_payment_ids(self):
        for rec in self:
            if (rec.state != 'posted') :
                rec.invoice_payment_ids = False
            else:
                pay_term_lines = rec.line_ids\
                    .filtered(lambda line: line.account_internal_type in ('receivable', 'payable'))
                account_moves_that_are_reconciled_with_this = self.env['account.move']  # based on account_partial_reconcile   debit with credit 
    # matched_debit_ids = fields.One2many('account.partial.reconcile', 'credit_move_id', string='Matched Debits',
        # help='Debit journal items that are matched with this journal item.', readonly=True)
    # matched_credit_ids = fields.One2many('account.partial.reconcile', 'debit_move_id', string='Matched Credits',
        # help='Credit journal items that are matched with this journal item.', readonly=True)
            
                for partial in pay_term_lines.matched_debit_ids:
                    account_moves_that_are_reconciled_with_this |= partial.debit_move_id.move_id
                for partial in pay_term_lines.matched_credit_ids:
                    account_moves_that_are_reconciled_with_this |= partial.credit_move_id.move_id
                payments = self.env['account.payment'].search([('move_id','in',account_moves_that_are_reconciled_with_this.ids)])
 
                rec.invoice_payment_ids = [(6,0,payments.ids)]
