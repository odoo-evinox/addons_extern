# Copyright 2011 Akretion, Sodexis
# Copyright 2018 Akretion
# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ExceptionRule(models.Model):
    _inherit = "exception.rule"

    model = fields.Selection(
        selection_add=[
            ("mrp.production", "Mrp Production"),
        ],
        ondelete={
            "mrp.production": "cascade",
        },
    )
    production_ids = fields.Many2many("mrp.production", string="Productions")


class MrpProduction(models.Model):
    _inherit = ["mrp.production", "base.exception"]
    _name = "mrp.production"

    @api.model
    def test_all_draft_orders(self):
        order_set = self.search([("state", "=", "draft")])
        order_set.detect_exceptions()
        return True

    @api.model
    def _reverse_field(self):
        return "production_ids"

    def detect_exceptions(self):
        all_exceptions = super().detect_exceptions()
        moves = self.mapped("move_raw_ids")
        all_exceptions += moves.detect_exceptions()
        return all_exceptions

    @api.constrains("ignore_exception", "move_raw_ids", "state")
    def _check_production_check_exception(self):
        orders = self.filtered(lambda s: s.state in ["done", "confirmed", "progress", "to_close"])
        if orders:
            orders._check_exception()

    @api.onchange("move_raw_ids")
    def onchange_ignore_exception(self):
        if self.state in ["done", "confirmed", "progress", "to_close"]:
            self.ignore_exception = False

    def action_confirm(self):
        if self.detect_exceptions() and not self.ignore_exception:
            return self._popup_exceptions()
        return super().action_confirm()

    def action_draft(self):
        res = super().action_draft()
        orders = self.filtered("ignore_exception")
        orders.write({"ignore_exception": False})
        return res

    def button_mark_done(self):
        if self.detect_exceptions():
            return self._popup_exceptions()
        return super().button_mark_done()

    @api.model
    def _get_popup_action(self):
        return self.env.ref("mrp_exception.action_mrp_exception_confirm").sudo()
