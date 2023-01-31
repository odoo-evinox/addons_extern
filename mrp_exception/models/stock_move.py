# © 2019 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import html

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    ignore_exception_move = fields.Boolean(
        related="raw_material_production_id.ignore_exception", store=True, string="Ignore Exceptions MRP"
    )

    def _get_main_records(self):
        stock_move_with_mrp = self.filtered(lambda l: l.raw_material_production_id)
        if stock_move_with_mrp:
            return stock_move_with_mrp.mapped("raw_material_production_id")
        return super()._get_main_records()

    @api.model
    def _reverse_field(self):
        stock_move_with_mrp = self.filtered(lambda l: l.raw_material_production_id)
        if stock_move_with_mrp:
            return "production_ids"
        return super()._reverse_field()

    def mrp_detect_exceptions(self, moves, rule):
        if rule.exception_type == "by_py_code":
            return moves._detect_exceptions_by_py_code(rule)
        elif rule.exception_type == "by_domain":
            return moves._detect_exceptions_by_domain(rule)

    def _detect_exceptions(self, rule):
        stock_move_with_mrp = self.filtered(lambda l: l.raw_material_production_id)
        if stock_move_with_mrp:
            mrp = self.mrp_detect_exceptions(stock_move_with_mrp, rule)
            if mrp:
                mrp.exception_ids = [(4, rule.id)]
                return mrp.mapped("raw_material_production_id")
            else:
                return self.env['mrp.production']
        else:
            return super()._detect_exceptions(rule)
