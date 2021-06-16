from odoo import fields, models
import time
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    created_invoice_id = fields.Many2one('account.move', readonly=1, help="This sale invoice was automatically created after this transfer was validated. Field used to print the invoice at picking. Invoice was created by pressing the create invoice from sale order.")
 
    def button_validate_with_backorder(self):
        return super(StockPicking,self).button_validate()
        
    def button_validate(self):
        self = self.with_context( 
                                 skip_backorder=True,  # this is skiping the create backorder viward
                                 #without bakcorder we must call process_cancel_backorder
                                 picking_ids_not_to_backorder=self.ids,
                          #   cancel_backorder=True,  used internaly to call pickings _action_done
                          # if picking_ids_not_to_backorder will cal with canecl_bakcorder=True
            
                                 )
        res =  super(StockPicking,self).button_validate()
        if res == True:
            #self._cr.commit()  # here is safe because the result is ok, no error if res ==True, is needed so the sale_id to have invoice_status, and to be able to create the invoice
#            time.sleep(0.04)
            for rec in self:
                sale_to_write = {}
                if rec.sale_id and rec.sale_id.invoice_status == "to invoice":  # was the probem with sale orders with is_downpayment. this last part is not giving the right value if no _cr.commit()
                    created_invoice = rec.sale_id._create_invoices(final=True)
#                    created_invoice.line_ids.filtered(lambda r: r.line_section='display_type').unlink()# still the problem from up and is not the case # is puting some lines with Down Payments
                    if rec.sale_id.authorized_transaction_ids:
                        tranzactions = rec.sale_id.authorized_transaction_ids.filtered(lambda r:r.state=='authorized')
                        paid = sum([x.amount for x in tranzactions])
                        paid_less, paid_more= 0,0
                        if created_invoice.amount_total - paid >0.01:
                            paid_less = created_invoice.amount_total - paid
                        elif created_invoice.amount_total - paid <-0.01:
                            paid_more = paid-created_invoice.amount_total
                        if  paid_less or  paid_more:
                            invoice_to_write = {'difference_between_order_and_deliverd':True}
                            sale_to_write.update({'difference_between_order_and_deliverd':True}) 
                            if tranzactions[0].acquirer_id.provider == 'on_delivery':  # here we are going to change the sum because is not yet paid
                                tranzactions[0].amount = tranzactions[0].amount + paid_less - paid_more
                                paid_less, paid_more= 0,0
                            else:  # is bank ??
                                invoice_to_write.update({'paid_less':paid_less, 'paid_more':paid_more})
                                sale_to_write = {'paid_less':paid_less, 'paid_more':paid_more}
                                if paid_more:
                                    # we create a line with advance 
                                    #invoice_to_write['line_ids'] = [(0,0{ 'name': 'Paid more',
                                            # 'type': 'service',
                                            # 'invoice_policy': 'order',
                                            # 'property_account_income_id': self.deposit_account_id.id,
                                            # 'taxes_id': [(6, 0, self.deposit_taxes_id.ids)],
                                            # 'company_id': False,},]
                                    pass
                                created_invoice.write(invoice_to_write)
                                    
                    
                    res_post_invoice = created_invoice.action_post()
                    rec.write({'created_invoice_id':created_invoice.id})
                    if sale_to_write:
                        rec.sale_id.write(sale_to_write)
                    rec.sale_id.write(sale_to_write)
                    if rec.sale_id.authorized_transaction_ids:
                        created_invoice.payment_action_capture()
                    
                    # if it had a payment.transaction if is from bank do the recociliation
                    # if is payment on delivery, change the payment transaction to have the same value and reconciliation
                    
            
        return res
    
    
    def print_created_invoice(self):
        self.ensure_one()
        if self.created_invoice_id:
            docids = self.created_invoice_id.ids
                               # 'account.account_invoices'  default invoice
            return self.env.ref('cbs_solutions_customization.action_invoice_with_receipt_report').report_action(docids, config=False)              # config should be false as otherwise it will call configuration wizard that works weirdly
        else:
            raise ValidationError(f"No invoice created from this picking={self} state={self.state}")

            