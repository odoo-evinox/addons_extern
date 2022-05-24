# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def button_create_landed_costs(self):
        """Create a `stock.landed.cost` record associated to the account move of `self`, each
        `stock.landed.costs` lines mirroring the current `account.move.line` of self.
        """

        res = super().button_create_landed_costs()
        landed_cost = self.env['stock.landed.cost'].browse(res.get('res_id'))
        if landed_cost:
            picking_invoice_ids = self.line_ids.mapped('purchase_line_id').mapped('order_id').mapped('picking_ids')
            picking_landed_cost_ids = self.env['stock.landed.cost'].search([('state', '=', 'done')]).mapped('picking_ids')
            landed_cost.picking_ids = picking_invoice_ids.filtered(lambda l: l not in picking_landed_cost_ids and l.state == 'done')
            for line in landed_cost.cost_lines:
                invoice_line = self.line_ids.filtered(lambda l: l.product_id == line.product_id)
                if invoice_line:
                    line.account_id = invoice_line[0].account_id
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('is_landed_costs_line')
    def _onchange_is_landed_costs_line(self):
        res = super()._onchange_is_landed_costs_line()
        if self.product_type == 'service' and self.is_landed_costs_line:
            accounts = self.product_id.product_tmpl_id._get_product_accounts()
            self.account_id = accounts['expense']
        return res
