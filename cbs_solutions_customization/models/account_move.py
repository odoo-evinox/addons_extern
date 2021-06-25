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

    cache_receipt_id = fields.Many2one("account.payment",compute="_compute_cache_receipt_id")
    
    def _compute_cache_receipt_id(self):
        for rec in self:
            if (rec.state != 'posted') or (rec.payment_state not in ['paid','in_payment']) or (
                (rec.move_type not in ['out_invoice', 'out_refund', 'out_receipt', 'in_receipt'])):
                rec.cache_receipt_id = False
            else:
                resp = json.loads(rec.invoice_payments_widget)
                if resp.get('outstanding')==False and len(resp['content'])==1 :
                    cache_receipt_id = resp['content'][0]['account_payment_id']
                    cache_receipt = self.env['account.payment'].browse(cache_receipt_id)
                    if cache_receipt.journal_id.type == 'cash':
                        rec.cache_receipt_id = cache_receipt
                    else:
                        rec.cache_receipt_id = False
                else:
                    rec.cache_receipt_id = False    
            # payments_widget_vals = {'title': _('Less Payment'), 'outstanding': False, 'content': []}
            #
            # if move.state == 'posted' and move.is_invoice(include_receipts=True):
                # payments_widget_vals['content'] = move._get_reconciled_info_JSON_values()
                #
            # if payments_widget_vals['content']:
                # move.invoice_payments_widget = json.dumps(payments_widget_vals, default=date_utils.json_default)
            # else:
                # move.invoice_payments_widget = json.dumps(False)
                #
                #
                #
