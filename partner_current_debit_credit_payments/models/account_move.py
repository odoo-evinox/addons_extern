from odoo import fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        for rec in self:
            rec.partner_id.check_over_credit_limit(with_this_sum = rec.amount_total_signed)
        return super().action_post()
