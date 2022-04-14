# Copyright (C) 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).


from odoo import models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_confirmation_values(self):
        res = super()._prepare_confirmation_values()
        if "date_order" in res:
            res.pop("date_order")
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_procurement_values(self, group_id=False):
        """ Update date planned with the one from sale order.
        """
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        if values.get("date_planned") != self.order_id.date_order:
            values["date_planned"] = self.order_id.date_order
        return values
