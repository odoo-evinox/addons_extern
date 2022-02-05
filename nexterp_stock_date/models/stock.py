# Copyright (C) 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from datetime import datetime

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    date = fields.Datetime('Processing Date')

    @api.depends('move_lines.state', 'move_lines.date', 'move_type')
    def _compute_scheduled_date(self):
        super()._compute_scheduled_date()
        for picking in self:
            picking.date = picking.scheduled_date

    def _action_done(self):
        """Update date_done from date field """
        res = super()._action_done()
        for picking in self:
            picking.date_done = picking.date
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    def get_move_date(self):
        self.ensure_one()
        new_date = self.date
        if self.picking_id:
            new_date = self.picking_id.date
        elif self.inventory_id:
            new_date = self.inventory_id.accounting_date
        elif "raw_material_production_id" in self._fields:
            if self.raw_material_production_id:
                new_date = self.raw_material_production_id.date_planned_start
            elif self.production_id:
                new_date = self.production_id.date_planned_start
        return new_date

    def _action_done(self, cancel_backorder=False):
        moves_todo = super()._action_done(cancel_backorder=cancel_backorder)
        for move in moves_todo:
            move.date = move.get_move_date()
        return moves_todo

    def _trigger_assign(self):
        res = super()._trigger_assign()
        for move in self:
            move.date = move.get_move_date()
        return res

    def _get_price_unit(self):
        # Update price unit for purchases in different currencies with the
        # reception date.
        if self.picking_id.date and self.purchase_line_id:
            po_line = self.purchase_line_id
            order = po_line.order_id
            price_unit = po_line.price_unit
            if po_line.taxes_id:
                price_unit = po_line.taxes_id.with_context(round=False).compute_all(
                    price_unit,
                    currency=order.currency_id,
                    quantity=1.0,
                    product=po_line.product_id,
                    partner=order.partner_id,
                )["total_excluded"]
            if po_line.product_uom.id != po_line.product_id.uom_id.id:
                price_unit *= (
                    po_line.product_uom.factor / po_line.product_id.uom_id.factor
                )
            if order.currency_id != order.company_id.currency_id:
                price_unit = order.currency_id._convert(
                    price_unit,
                    order.company_id.currency_id,
                    self.company_id,
                    self.picking_id.date,
                    round=False,
                )
            self.write(
                {
                    "price_unit": price_unit,
                    "date": self.picking_id.date,
                }
            )
            return price_unit
        return super()._get_price_unit()

    def _account_entry_move(self, qty, description, svl_id, cost):
        self.ensure_one()
        val_date = self.get_move_date()
        self = self.with_context(force_period_date=val_date)
        return super(StockMove, self)._account_entry_move(qty, description, svl_id, cost)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        res = super()._action_done()
        for move_line in self.exists():
            if move_line.move_id:
                move_line.date = move_line.move_id.get_move_date()
        return res


# todo check to update in_date with moves dates
# class StockQuant(models.Model):
#     _inherit = "stock.quant"
#
#     @api.depends("company_id", "location_id", "owner_id", "product_id", "quantity")
#     def _compute_value(self):
#         quants_with_loc = self.filtered(lambda q: q.location_id)
#         for quant in quants_with_loc:
#             super(
#                 StockQuant, quant.with_context(location_id=quant.location_id.id)
#             )._compute_value()
#         return super(StockQuant, self - quants_with_loc)._compute_value()


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"
    _log_access = False

    create_date = fields.Datetime('Created on', index=True, readonly=True)
    create_uid = fields.Many2one('res.users', 'Created by', index=True, readonly=True)
    write_date = fields.Datetime('Last Updated on', index=True, readonly=True)
    write_uid = fields.Many2one('res.users', 'Last Updated by', index=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            val_date = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            if values.get("stock_move_id"):
                move = self.env["stock.move"].browse(values["stock_move_id"])
                val_date = move.get_move_date()
            values.update({
                'create_uid': self._uid,
                "create_date": val_date,
                'write_uid': self._uid,
                'write_date': val_date,
            })
        return super().create(vals_list)

    def write(self, vals):
        if not vals.get('write_uid'):
            vals['write_uid'] = self._uid
        if not vals.get('write_date'):
            vals['write_date'] = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        return super().write(vals)