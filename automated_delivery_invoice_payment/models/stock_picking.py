from odoo import fields, models
import time

class StockPicking(models.Model):
    _inherit = "stock.picking"
 
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
            self._cr.commit()  # here is safe becuse the result is ok, no error if res ==True, is needed so the sale_id to have invoice_status, and to be able to create the invoice
            time.sleep(0.04)
            for rec in self:
                if rec.sale_id rec.sale_id.invoice_status == "to invoice":  # was the probem with sale orders with is_downpayment. this last part is not giving the right value if no _cr.commit()
                    created_invoice = rec.sale_id._create_invoices(final=True)
#                    created_invoice.line_ids.filtered(lambda r: r.line_section='display_type').unlink()# still the problem from up and is not the case # is puting some lines with Down Payments
                    res_post_invoice = created_invoice.action_post()
                    # if it had a payment.transaction if is from bank do the recociliation
                    # if is payment on delivery, change the payment transaction to have the same value and reconciliation
                    
            
        return res
    
    
