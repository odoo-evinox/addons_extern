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


class BaseExceptionMethod(models.AbstractModel):
    _inherit = "base.exception.method"

    def detect_exceptions(self):
        """List all exception_ids applied on self
        Exception ids are also written on records
        """
        rules = self.env["exception.rule"].sudo().search(self._rule_domain())
        all_exception_ids = []
        rules_to_remove = {}
        rules_to_add = {}
        for rule in rules:
            records_with_exception = self._detect_exceptions(rule)
            reverse_field = self._reverse_field()
            main_records = self._get_main_records()
            if main_records and rule[reverse_field]:
                commons = main_records & rule[reverse_field]
                to_remove = commons - records_with_exception
                to_add = records_with_exception - commons
                # we expect to always work on the same model type
                if rule.id not in rules_to_remove:
                    rules_to_remove[rule.id] = main_records.browse()
                rules_to_remove[rule.id] |= to_remove
                if rule.id not in rules_to_add:
                    rules_to_add[rule.id] = main_records.browse()
                rules_to_add[rule.id] |= to_add
                if records_with_exception:
                    all_exception_ids.append(rule.id)
        for rule_id, records in rules_to_remove.items():
            records.write({"exception_ids": [(3, rule_id)]})
        for rule_id, records in rules_to_add.items():
            records.write({"exception_ids": [(4, rule_id)]})
        return all_exception_ids


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

    def button_mark_done(self):
        if self.detect_exceptions():
            return self._popup_exceptions()
        return super().button_mark_done()
    
    def _mrp_get_lines(self):
        self.ensure_one()
        return self.move_raw_ids

    @api.model
    def _get_popup_action(self):
        return self.env.ref("mrp_exception.action_mrp_exception_confirm").sudo()
