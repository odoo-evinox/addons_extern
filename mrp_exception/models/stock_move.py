# © 2019 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import html

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    exception_ids = fields.Many2many(
        "exception.rule", string="Exceptions", copy=False, readonly=True
    )
    ignore_exception_move = fields.Boolean(
        related="raw_material_production_id.ignore_exception", store=True, string="Ignore Exceptions MRP"
    )

    def _get_main_records(self):
        stock_move_with_mrp = self.filtered(lambda l: l.raw_material_production_id)
        stock_move_with_picking = self.filtered(lambda l: l.picking_id)
        if stock_move_with_picking:
            return super(StockMove, stock_move_with_picking)._get_main_records()
        if stock_move_with_mrp:
            return stock_move_with_mrp.mapped("raw_material_production_id")

    @api.model
    def _reverse_field(self):
        stock_move_with_mrp = self.filtered(lambda l: l.raw_material_production_id)
        stock_move_with_picking = self.filtered(lambda l: l.picking_id)
        if stock_move_with_picking:
            return super()._reverse_field()
        if stock_move_with_mrp:
            return "production_ids"

    def mrp_detect_exceptions(self, rule):
        if rule.exception_type == "by_py_code":
            return self._detect_exceptions_by_py_code(rule)
        elif rule.exception_type == "by_domain":
            return self._detect_exceptions_by_domain(rule)

    def _detect_exceptions(self, rule):
        stock_move_with_mrp = self.filtered(lambda l: l.raw_material_production_id)
        stock_move_with_picking = self.filtered(lambda l: l.picking_id)
        if stock_move_with_picking:
            return super(StockMove, stock_move_with_picking)._detect_exceptions(rule)
        if stock_move_with_mrp:
            stock_move_with_exception = stock_move_with_mrp.mrp_detect_exceptions(rule)
            stock_move_with_exception.exception_ids = [(4, rule.id)]
            return stock_move_with_exception.mapped("raw_material_production_id")
