from odoo import fields, models
import time
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

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
        if res == True and not self.env.context.get('skip_create_invoice_after_transfer'):
            for rec in self.sudo(): # sudo neccesary because not all inventory workers have also accounting rights
                if rec.sale_id and rec.sale_id.invoice_status == "to invoice":  
                    paid_less, paid_more= 0,0
                    sale_to_write = {'paid_less':paid_less, 'paid_more':paid_more, 'difference_between_order_and_deliverd':False}
                    
                    # WE ARE GOING TO AUTOMATICALY CREATE INVOICE ONLY IF IS NOT FROM 
                    try:
                        created_invoice = rec.sale_id._create_invoices(final=True)
                    except Exception as ex:
                        _logger.error(f'we could not create the invoice from picking={rec} validate because of error:{ex}.\n Normally another module has some requirements and can not be done this and also that ( rma for example with a replace and refund )')
                        created_invoice = ''
                        continue
                    if created_invoice and type(created_invoice) is not dict:  # can be the case when it returns a page with error an not an error
                        if rec.sale_id.authorized_transaction_ids:
                            authorized_tranzactions = rec.sale_id.authorized_transaction_ids.filtered(lambda r:r.state=='authorized')
                            paid = sum([x.amount for x in authorized_tranzactions])
                            if created_invoice.amount_total - paid >0.01:
                                paid_less = created_invoice.amount_total - paid
                            elif created_invoice.amount_total - paid <-0.01:
                                paid_more = paid-created_invoice.amount_total
                            if  paid_less or  paid_more:
                                sale_to_write.update({'difference_between_order_and_deliverd':True})
                                # here we are going to change the sum because is not yet paid
                                if authorized_tranzactions[0].acquirer_id.provider == 'on_delivery':  
                                    authorized_tranzactions[0].amount = authorized_tranzactions[0].amount + paid_less - paid_more
                                    paid_less, paid_more= 0,0
                                else:  # is bank ??
                                    sale_to_write.update({'paid_less':paid_less, 'paid_more':paid_more})
                                    if paid_more:
                                        # we could create a line with advance ; or another invoice
                                        pass
                                sale_to_write.update({'paid_less':paid_less, 'paid_more':paid_more})            
                                invoice_to_write = sale_to_write.copy()
                                if paid_less == paid_more:
                                    invoice_to_write['resolved_difference'] = f'Modified payment on delivery from {paid} to {created_invoice.amount_total}' 
                                created_invoice.write(invoice_to_write)
                        try:
                            res_post_invoice = created_invoice.action_post()
                        except Exception as ex:
                            _logger.error(f'we could not post the invoice from picking={rec}, invoice {created_invoice}  because of error:{ex}.\n Normally another module has some requirements and can not be done this and also that ')
                            continue
                         # for the case that the invoice is already posted( from other modules like rma
                        # we write in sale_order all the time because can have older status on it
                        rec.sale_id.write(sale_to_write)
                        # we write the cread invoice in picking
                        rec.write({'created_invoice_id':created_invoice.id})  
                    

                        # set the transaction as done and link it with the invoice
                        if rec.sale_id.authorized_transaction_ids:
#20211027   modified with try because the the payment_action_capure at sale order for bt pay is giving error Payment must be in approved state
                            try:
                                created_invoice.payment_action_capture()
                            except Exception as ex: 
                                rec.sale_id.message_post(body=f"capture tranzaction error: {str(ex)}",message_type='notification')
                    # if it had a payment.transaction if is from bank do the recociliation
                    # if is payment on delivery, change the payment transaction to have the same value and reconciliation
                    
            
        return res
    
    
    def print_created_invoice(self):
        self.ensure_one()
        if self.created_invoice_id:
            docids = self.created_invoice_id.ids
                               # 'account.account_invoices'  default invoice
#            return self.env.ref('cbs_solutions_customization.action_invoice_with_receipt_report').report_action(docids, config=False)              # config should be false as otherwise it will call configuration wizard that works weirdly
            return self.env.ref('account.account_invoices').report_action(docids, config=False)              # config should be false as otherwise it will call configuration wizard that works weirdly
        else:
            raise ValidationError(f"No invoice created from this picking={self} state={self.state}")

            