# Copyright 2014-2018 Tecnativa - Pedro M. Baeza
# Copyright 2015 Antonio Espinosa - Tecnativa <antonio.espinosa@tecnativa.com>
# Copyright 2018 Luis M. Ontalba - Tecnativa <luis.martinez@tecnativa.com>
# Copyright 2016-2018 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# 2021 NextERP

from odoo import fields, models
from odoo.exceptions import ValidationError

# creating some fields to have also valued purchases


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_aggregated_product_quantities(self, **kwargs):
        """giving also the purchase_price needed for showing in report
        this function is used in aggregated lines template
        """

        if (not self.picking_id.installed_stock_picking_report_valued) or (
            not self.picking_id.purchase_id
        ):
            return super()._get_aggregated_product_quantities(**kwargs)
        else:
            "rewrite of original function to add also price"
            aggregated_move_lines = {}
            for move_line in self:
                name = move_line.product_id.display_name
                description = move_line.move_id.description_picking
                if description == name or description == move_line.product_id.name:
                    description = False
                uom = move_line.product_uom_id
                line_key = (
                    str(move_line.product_id.id)
                    + "_"
                    + name
                    + (description or "")
                    + "uom "
                    + str(uom.id)
                )

                if line_key not in aggregated_move_lines:
                    aggregated_move_lines[line_key] = {
                        "name": name,
                        "description": description,
                        "qty_done": move_line.qty_done,
                        "product_uom": uom.name,
                        "product": move_line.product_id,
                    }
                    # added by us for purchase
                    aggregated_move_lines[line_key].update(
                        {
                            "purchase_price_unit": move_line.purchase_price_unit,
                            "purchase_tax_description": move_line.purchase_tax_description,
                            "purchase_price_subtotal": move_line.purchase_price_subtotal,
                            "purchase_price_tax": move_line.purchase_price_tax,
                        }
                    )

                else:
                    aggregated_move_lines[line_key]["qty_done"] += move_line.qty_done
                    # added by us
                    aggregated_move_lines[line_key][
                        "purchase_price_subtotal"
                    ] += move_line.purchase_price_subtotal
                    aggregated_move_lines[line_key][
                        "purchase_price_tax"
                    ] += move_line.purchase_price_tax

            return aggregated_move_lines
        return {}

    def _get_unit_price_internal_consumption(self):
        if self.move_id._is_internal_transfer():
            pl = self.move_id.picking_id.partner_id.property_product_pricelist
            return pl.price_get(self.move_id.product_id.id, self.move_id.product_qty)[
                pl.id
            ]
        elif self.move_id._is_consumption():
            avg = 0
            if self.move_id.stock_valuation_layer_ids:
                avg = sum(
                    [
                        svl.quantity * svl.unit_cost
                        for svl in self.move_id.stock_valuation_layer_ids
                    ]
                ) / sum(
                    [svl.quantity for svl in self.move_id.stock_valuation_layer_ids]
                )
            return avg
        return 0
