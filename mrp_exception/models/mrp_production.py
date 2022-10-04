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
    def _reverse_field(self):
        return "production_ids"

    def detect_exceptions(self):
        all_exceptions = super().detect_exceptions()
        lines = self.mapped("move_raw_ids")
        exceptions = lines.detect_exceptions()
        if exceptions:
            all_exceptions += exceptions
        return all_exceptions

    @api.model
    def test_all_draft_orders(self):
        order_set = self.search([("state", "=", "draft")])
        order_set.detect_exceptions()
        return True

    def _fields_trigger_check_exception(self):
        return ["ignore_exception", "move_raw_ids", "state"]

    def _check_production_check_exception(self, vals):
        check_exceptions = any(
            field in vals for field in self._fields_trigger_check_exception()
        )
        if check_exceptions:
            self.production_check_exception()

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._check_production_check_exception(vals)
        return record

    def write(self, vals):
        result = super().write(vals)
        self._check_production_check_exception(vals)
        return result

    def production_check_exception(self):
        orders = self.filtered(lambda s: s.state == "done")
        if orders:
            orders._check_exception()

    @api.onchange("move_raw_ids")
    def onchange_ignore_exception(self):
        if self.state == "done":
            self.ignore_exception = False

    def action_confirm(self):
        if self.detect_exceptions():
            return self._popup_exceptions()
        return super().action_confirm()

    def action_draft(self):
        res = super().action_draft()
        orders = self.filtered("ignore_exception")
        orders.write({"ignore_exception": False})
        return res

    def _mrp_get_lines(self):
        self.ensure_one()
        return self.move_raw_ids

    @api.model
    def _get_popup_action(self):
        return self.env.ref("mrp_exception.action_mrp_exception_confirm")
