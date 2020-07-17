# Copyright 2014-2018 Tecnativa - Pedro M. Baeza
# Copyright 2015 Antonio Espinosa - Tecnativa <antonio.espinosa@tecnativa.com>
# Copyright 2018 Luis M. Ontalba - Tecnativa <luis.martinez@tecnativa.com>
# Copyright 2016-2018 Carlos Dauden - Tecnativa <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
 
  # list_price=sales price taken from product filed lst_price  is the price from pricelist
    list_price = fields.Float( related="product_id.list_price")    
    margin = fields.Float(string='Margin [%]', compute="_compute_sale_order_line_fields", compute_sudo=True)
    sale_with_magin_price_total = fields.Float(compute="_compute_sale_order_line_fields", compute_sudo=True)


    def _compute_sale_order_line_fields(self):
        """add also fields for margin if the destination location is type store
        """
        for line in self:
            margin = 0
            sale_with_magin_price_total = 0
            if 'sale_price_unit' in  self.fields and 'sale_line' in  self.fields:
                # means that the stock_picking report is installed
                super()._compute_amount_all() # the before behavior 
                sale_line = line.sale_line
                price_unit = (sale_line.price_subtotal / sale_line.product_uom_qty if sale_line.product_uom_qty  else sale_line.price_reduce)
                margin = (self.list_price - price_unit)/100
###### aici e greist este alt stock_pircking_repot  that is function also on purchase                
            sale_line = line.sale_line
            price_unit = (
                sale_line.price_subtotal / sale_line.product_uom_qty
                if sale_line.product_uom_qty
                else sale_line.price_reduce
            )
            taxes = line.sale_tax_id.compute_all(
                price_unit=price_unit,
                currency=line.currency_id,
                quantity=line.qty_done or line.product_qty,
                product=line.product_id,
                partner=sale_line.order_id.partner_shipping_id,
            )
            if sale_line.company_id.tax_calculation_rounding_method == (
                "round_globally"
            ):
                price_tax = sum(t.get("amount", 0.0) for t in taxes.get("taxes", []))
            else:
                price_tax = taxes["total_included"] - taxes["total_excluded"]
            line.update(
                {
                    "sale_tax_description": ", ".join(
                        t.name or t.description for t in line.sale_tax_id
                    ),
                    "sale_price_subtotal": taxes["total_excluded"],
                    "sale_price_tax": price_tax,
                    "sale_price_total": taxes["total_included"],
                }
            )
