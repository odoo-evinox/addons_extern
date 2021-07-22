from odoo import fields, models,_,api
import time
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"
    
    def action_post_bank(self):
        self.action_post_cache('bank')

    def action_post_cache(self,journal='cash'):
        original = super(AccountMove,self).action_post()
        account_journal = self.env['account.journal'].search([('company_id', '=', self.company_id.id),('type','=',journal)],order='id', limit=1)   
        for rec in self:
            if not rec.amount_total and not rec.amount_residual:
                continue
                rec.action_register_payment() 
            PaymentWizard = self.env['account.payment.register']
            payment_wizard = PaymentWizard.with_context(active_model='account.move').with_context(active_ids=rec.ids).create({
                'payment_date': rec.invoice_date,
                'amount':rec.amount_total, 
                'communication': 'payment of '+rec.name,
                'group_payment': False,
                'journal_id': account_journal.id,
                # == Fields given through the context ==
                'partner_id': rec.partner_id.id,
                } )
        # return {
            # 'name': _('Register Payment'),
            # 'res_model': 'account.payment.register',
            # 'view_mode': 'form',
            # 'context': {
   # #             'active_model': 'account.move',
    # #            'active_ids': self.ids,
            # },
            # 'target': 'new',
            # 'res_id':payment_wizard.id,
            # 'type': 'ir.actions.act_window',
        # }
        res = payment_wizard.action_create_payments()
        return original
            