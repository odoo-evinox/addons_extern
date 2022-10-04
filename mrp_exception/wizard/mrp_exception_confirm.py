# Copyright 2011 Akretion, Sodexis
# Copyright 2018 Akretion
# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class MrpExceptionConfirm(models.TransientModel):
    _name = "mrp.exception.confirm"
    _inherit = ["exception.rule.confirm"]
    _description = "Mrp exception confirm wizard"

    related_model_id = fields.Many2one("mrp.production", "Production")

    def action_confirm(self):
        self.ensure_one()
        if self.ignore:
            self.related_model_id.ignore_exception = True
        return super().action_confirm()
