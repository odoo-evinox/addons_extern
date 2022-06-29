# Copyright (C) 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models
from collections import defaultdict
from odoo.tools import float_is_zero

import logging
_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.depends("stock_valuation_layer_ids")
    @api.depends_context("to_date", "company", "location_id")
    def _compute_value_svl(self):
        """Compute `value_svl` and `quantity_svl`.
        Overwrite to allow multiple prices per location
        """
        if self.env.context.get("location_id"):
            company_id = self.env.company.id
            domain = [
                ("product_id", "in", self.ids),
                ("company_id", "=", company_id),
                ("remaining_qty", ">", 0),
                ("location_dest_id", "=", self.env.context.get("location_id")),
            ]
            if self.env.context.get("to_date"):
                to_date = fields.Datetime.to_datetime(self.env.context["to_date"])
                domain.append(("create_date", "<=", to_date))
            groups = self.env["stock.valuation.layer"].read_group(
                domain, ["remaining_value:sum", "remaining_qty:sum"], ["product_id"]
            )
            products = self.browse()
            for group in groups:
                product = self.browse(group["product_id"][0])
                product.value_svl = self.env.company.currency_id.round(
                    group["remaining_value"]
                )
                product.quantity_svl = group["remaining_qty"]
                products |= product
            remaining = self - products
            remaining.value_svl = 0
            remaining.quantity_svl = 0
        else:
            super()._compute_value_svl()


    def _run_fifo(self, quantity, company):
        self.ensure_one()

        if self.env.context.get('location_id') or self.env.context.get('average_cost_method_change'):
            # Find back incoming stock valuation layers (called candidates here) to value `quantity`.
            qty_to_take_on_candidates = quantity

            #customized
            candidates_domain = [
                ('product_id', '=', self.id),
                ('remaining_qty', '>', 0),
                ('company_id', '=', company.id),
            ]

            if self.env.context.get('location_id'):
                candidates_domain.append(('location_dest_id', '=', self.env.context['location_id']))


            candidates = self.env['stock.valuation.layer'].sudo().search(candidates_domain)

            # If no candidates in main location, search for sublocations
            if not candidates and self.env.context.get('location_id'):
                location = self.env['stock.location'].browse(self.env.context['location_id'])
                child_locations = self.env['stock.location'].search([('location_id', 'child_of', location.id)])
                candidates_domain = [
                    ('product_id', '=', self.id),
                    ('remaining_qty', '>', 0),
                    ('company_id', '=', company.id),
                    ('location_dest_id', 'in', child_locations.ids)
                ]
                candidates = self.env['stock.valuation.layer'].sudo().search(candidates_domain)
            #----------

            new_standard_price = 0
            tmp_value = 0  # to accumulate the value taken on the candidates
            #customized
            new_standard_price_avg = 0
            if candidates and 'average_cost_method_change' in self.env.context:
                new_standard_price_avg = self.env.context['average_cost_method_change']
            #----------

            for candidate in candidates:
                qty_taken_on_candidate = min(qty_to_take_on_candidates, candidate.remaining_qty)

                candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
                new_standard_price = candidate_unit_cost
                value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
                value_taken_on_candidate = candidate.currency_id.round(value_taken_on_candidate)
                new_remaining_value = candidate.remaining_value - value_taken_on_candidate

                candidate_vals = {
                    'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                    'remaining_value': new_remaining_value,
                }

                candidate.write(candidate_vals)

                qty_to_take_on_candidates -= qty_taken_on_candidate
                tmp_value += value_taken_on_candidate

                if float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
                    if float_is_zero(candidate.remaining_qty, precision_rounding=self.uom_id.rounding):
                        next_candidates = candidates.filtered(lambda svl: svl.remaining_qty > 0)
                        new_standard_price = next_candidates and next_candidates[0].unit_cost or new_standard_price
                    break

            # Update the standard price with the price of the last used candidate, if any.
             ## customized
            if new_standard_price and self.cost_method == 'fifo':
                if 'average_cost_method_change' in self.env.context:
                    self.sudo().with_company(company.id).with_context(
                        disable_auto_svl=True).standard_price = new_standard_price_avg
                else:
                    new_standard_price_avg = new_standard_price
                    self.sudo().with_company(company.id).with_context(
                        disable_auto_svl=True).standard_price = new_standard_price                    
            #-------------

            # If there's still quantity to value but we're out of candidates, we fall in the
            # negative stock use case. We chose to value the out move at the price of the
            # last out and a correction entry will be made once `_fifo_vacuum` is called.
            vals = {}
            if float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
                vals = {
                    'value': -tmp_value,
                    'unit_cost': tmp_value / quantity,
                }
            else:
                assert qty_to_take_on_candidates > 0

                ## customized
                last_fifo_price = new_standard_price_avg or self.standard_price
                #------------

                negative_stock_value = last_fifo_price * -qty_to_take_on_candidates
                tmp_value += abs(negative_stock_value)
                vals = {
                    'remaining_qty': -qty_to_take_on_candidates,
                    'value': -tmp_value,
                    'unit_cost': last_fifo_price,
                }
            return vals

        return super()._run_fifo(quantity, company)


    #TODO check context also here
    # def _run_fifo_vacuum(self, company=None): 
    #......


    @api.model
    def _svl_empty_stock(self, description, product_category=None, product_template=None):
        impacted_product_ids = []
        impacted_products = self.env['product.product']
        products_orig_quantity_svl = defaultdict(list)

        # get the impacted products
        domain = [('type', '=', 'product')]
        if product_category is not None:
            domain += [('categ_id', '=', product_category.id)]
        elif product_template is not None:
            domain += [('product_tmpl_id', '=', product_template.id)]
        else:
            raise ValueError()

        #customized code
        locations = self.env['stock.quant'].search([('location_id.usage', '=', 'internal')]).mapped('location_id')
        empty_stock_svl_list = []       
        for location in locations:

            products = self.env['product.product'].search_read(domain, ['quantity_svl'])

            for product in products:
                prod = self.env['product.product'].browse(product['id'])

                quant = self.env['stock.quant'].search([('location_id', '=', location.id),
                                                        ('product_id', '=', prod.id)])
                if quant:
                    products_orig_quantity_svl[product['id']].append([location.id, sum(quant.mapped('quantity'))])

                if float_is_zero(prod.quantity_svl, precision_rounding=prod.uom_id.rounding):
                    continue

                impacted_product_ids.append(product['id'])
                

            impacted_products |= self.env['product.product'].browse(impacted_product_ids)
            # empty out the stock for the impacted products
            for product in impacted_products:
                avg = product.value_svl / product.quantity_svl

                product = product.with_context(
                    location_id=location.id, 
                    average_cost_method_change=avg
                    )

                # FIXME sle: why not use products_orig_quantity_svl here?
                if float_is_zero(product.quantity_svl, precision_rounding=product.uom_id.rounding):
                    # FIXME: create an empty layer to track the change?
                    continue


                svsl_vals = product._prepare_out_svl_vals(product.quantity_svl, self.env.company)
                svsl_vals['description'] = description + svsl_vals.pop('rounding_adjustment', '')
                svsl_vals['company_id'] = self.env.company.id
                svsl_vals['location_id'] = location.id
                svsl_vals['location_dest_id'] = location.id
                empty_stock_svl_list.append(svsl_vals)
        #----------

        return empty_stock_svl_list, products_orig_quantity_svl, impacted_products


    def _svl_replenish_stock(self, description, products_orig_quantity_svl):
        refill_stock_svl_list = []
        for product in self:
            for location_id, quantity_svl in products_orig_quantity_svl[product.id]:
                if quantity_svl:
                    svl_vals = product._prepare_in_svl_vals(quantity_svl, product.standard_price)
                    svl_vals['description'] = description
                    svl_vals['company_id'] = self.env.company.id
                    svl_vals['location_id'] = location_id
                    svl_vals['location_dest_id'] = location_id
                    refill_stock_svl_list.append(svl_vals)
        return refill_stock_svl_list