from odoo import fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def write(self,values):
        state = values.get('state')
        if state in ['sent','done','sale']:
            for rec in self:
                rec.partner_id.check_over_credit_limit(with_this_sum = rec.amount_total)
        return super().write(values)  
