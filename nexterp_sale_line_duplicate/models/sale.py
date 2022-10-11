# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).
from odoo import _, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def action_duplicate(self):
        res_id = self.env["sale.order.line.duplicate"].create({"sale_line_id": self.id})
        return {
            "name": _("Duplicate Sales Order Line"),
            "view_mode": "form",
            "res_model": "sale.order.line.duplicate",
            "view_id": self.env.ref(
                "nexterp_sale_line_duplicate.sale_line_duplicate_view_form"
            ).id,
            "type": "ir.actions.act_window",
            "context": dict(self._context),
            "res_id": res_id.id,
            "target": "new",
        }
