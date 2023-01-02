# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_tax_id(self):
        super()._compute_tax_id()
        for line in self:
            if not line.tax_id and line.company_id.parent_id:
                comp = line.company_id.parent_id
                line = line.with_company(comp)
                fpos = (
                    line.order_id.fiscal_position_id
                    or line.order_id.fiscal_position_id.get_fiscal_position(
                        line.order_partner_id.id
                    )
                )
                # If company_id is set, always filter taxes by the company
                taxes = line.product_id.taxes_id.filtered(
                    lambda t: t.company_id == comp
                )
                line.tax_id = fpos.map_tax(
                    taxes, line.product_id, line.order_id.partner_shipping_id
                )
