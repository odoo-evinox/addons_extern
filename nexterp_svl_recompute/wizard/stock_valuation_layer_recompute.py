# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from collections import defaultdict



class SVLRecomputeLocation(models.TransientModel):
    _name = 'svl.recompute.location'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
    )
    svl_recompute_id = fields.Many2one(
        'svl.recompute',
        string='Field Label',
    )


class StockValuationLayerRecompute(models.TransientModel):
    _name = 'svl.recompute'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    product_id = fields.Many2one('product.product', "Related product", check_company=True)
    date_from = fields.Date("Recompute Start Date")
    location_ids = fields.One2many(
        'svl.recompute.location',
        'svl_recompute_id',
        string='Locations',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        locs = self.env['stock.location'].search([('usage', '=', 'internal')], order="id")
        location_ids = []
        idx = 10
        for loc in locs:
            location_ids.append((0, 0, {
                'sequence': idx, 'location_id': loc.id
            }))
            idx += 10
        res['location_ids'] = location_ids
        return res

    def buttton_do_correction(self):
        self._prepare_svls()
        self.action_start_recompute()
        self._fix_remaining_qty_value()
        self._finalize_svls()        

    def _prepare_svls(self):
        #backup unit_cost and value
        if self.product_id:
            products = self.product_id
        else:
            products = self.product_id or self.env['product.product'].search([])        

        locations = self.location_ids.mapped('location_id')        
        domain = ['&', 
                    ('product_id', 'in', products.ids), 
                    '|',
                        ('location_dest_id', 'in', locations.ids), 
                        ('location_id', "in", locations.ids),
                ]


        svls = self.env['stock.valuation.layer'].search(domain)
        for svl in svls:
            svl.new_unit_cost = svl.unit_cost
            svl.new_value = svl.value        
            svl.new_remaining_value = svl.remaining_value        
            svl.new_remaining_qty = svl.remaining_qty        

        # self._cr.execute("""
        #     DELETE from stock_valuation_layer where valued_type is null
        # """)
        # self._cr.execute("""
        #     UPDATE stock_quant sq set company_id = loc.company_id 
        #     FROM stock_location loc where sq.location_id = loc.id;
        # """)
        # self._cr.execute("""        
        #    UPDATE stock_valuation_layer set valued_type = 'consumption' 
        #    where valued_type = 'production_return';
        #""")
        # self._cr.execute("""        
        #    DELETE from stock_valuation_layer where description 
        #    like '%negative inventory%';
        #""")
        #self._cr.execute("""
        #   DELETE from stock_valuation_layer where description 
        #    like '%0 Qty Correction valuation%';
        #""")
        pass

    def action_start_recompute(self):
        if self.product_id:
            products = self.product_id
        else:
            products = self.product_id or self.env['product.product'].search([])
        locations = self.location_ids.mapped('location_id')

        for product in products:
            if product.cost_method == "fifo":
                for loc in locations:                
                    #self._run_fifo(product, loc)
                    pass
            if product.cost_method == "average":
                self._run_average(product, locations.ids)

        return True

    def _run_average(self, product, locations):
        self = self.sudo()
        date_from = fields.Datetime.to_datetime(self.date_from)
        avg = [0, 0]
        product = product.with_context(to_date=self.date_from)        
        if product.quantity_svl > 0.01:
            quantity_svl = round(product.quantity_svl, 2)            
            value_svl = round(product.value_svl, 2)
            avg = [round(value_svl / quantity_svl, 2), quantity_svl] 

        domain = ['&', 
                    '&',
                        ('product_id', '=', product.id), 
                        ('create_date', '>=', date_from),
                    '|',
                        '&',
                            ('location_dest_id', 'in', locations), 
                            ('quantity', '>', 0.001),
                        '&',
                            ('location_id', "in", locations),
                            ('quantity', '<', 0.001),
                ]

        svls = list(self.env['stock.valuation.layer'].search(domain).sorted(lambda svl: svl.create_date))

        while svls:
            svl = svls[0]

            if 'return' in svl.valued_type:
                orig_mv = svl.stock_move_id.move_orig_ids
                if orig_mv:
                    svl_orig = orig_mv.stock_valuation_layer_ids
                    val = abs(sum([s.value for s in svl_orig]))
                    qty = sum([s.quantity for s in svl_orig])
                    svl.value = round(svl.quantity * abs(val / qty), 2)
                    svl.unit_cost = round(abs(val / qty), 2)

            if (
                    svl.stock_move_id._is_in() or
                    (
                        svl.stock_move_id._is_internal_transfer()
                        and 
                        (
                            svl.stock_move_id.location_id.company_id != 
                            svl.stock_move_id.location_dest_id.company_id
                        )
                    )
                ):
                #update average cost
                old_value = avg[0] * avg[1]
                #include landed costs and price diffs
                svl_val = sum([s.value for s in (svl + svl.stock_valuation_layer_ids)])
                if (avg[1] + svl.quantity) > 0:
                    new_avg = (old_value + svl_val) / (avg[1] + svl.quantity)
                else:
                    new_avg = 0
                avg = [new_avg, avg[1] + svl.quantity]

            elif svl.stock_move_id._is_out():
                if avg[1] <= 0:
                    #move svl later, after a reception
                    
                    avg[1] = 0
                    idx = -1
                    svl_qty = abs(svl.quantity)
                    for i in range(len(svls)):
                        if svls[i].quantity > 0:
                            if svls[i].quantity >= svl_qty:
                                idx = i
                                break
                            else:
                                svl_qty -= svls[i].quantity
                    if idx != -1:
                        svls.insert(idx + 1, svl)
                    else:
                        print(f"NEGATIVE SVL: {svl.id} {svl.description}")
                        print(svls)
                        break
                else:
                    if 'return' not in svl.valued_type:
                        svl.unit_cost = round(avg[0], 2)
                        svl.value = round(avg[0] * svl.quantity, 2)
                    else:
                        if (avg[1] - abs(svl.quantity)) > 0:
                            avg[0] = (avg[0] * avg[1] - abs(svl.value)) / (avg[1] - abs(svl.quantity))
                        else:
                            avg[0] = 0
                    avg[1] = max(0, avg[1] - abs(svl.quantity))

            elif svl.stock_move_id._is_internal_transfer() and svl.quantity < 0:
                svl.unit_cost = round(avg[0], 2)
                svl.value = round(avg[0] * svl.quantity, 2)
                
                svl_plus = svl.stock_move_id.stock_valuation_layer_ids.filtered(lambda s: s.quantity > 0)
                svl_plus.unit_cost = round(avg[0], 2)
                svl_plus.value = round(svl_plus.quantity * avg[0], 2)

            svls = svls[1:]

    def _run_fifo(self, product, loc):
        #TODO
        svls_recreate_account_move = []

        date_from = fields.Datetime.to_datetime(self.date_from)
        date_domain = [('create_date', '>=', date_from)]
            
        should_restart_fifo = True
        while should_restart_fifo:
            avgs = dict(initial_avgs)
            should_restart_fifo = False

            domain_in = date_domain + [('product_id', '=', product.id), ("location_dest_id", "=", loc.id), ('quantity', '>', 0)]
            svl_loc_in = self.env['stock.valuation.layer'].search(domain_in)

            domain_out = date_domain + [('product_id', '=', product.id), ("location_id", "=", loc.id), ('quantity', '<', 0)]
            svl_loc_out = self.env['stock.valuation.layer'].search(domain_out)

            quantity = abs(sum(svl_loc_out.mapped('quantity')))

            svl_loc_in = svl_loc_in.sorted(lambda svl: svl.create_date)
            svl_loc_out = svl_loc_out.sorted(lambda svl: svl.create_date)

            # build fifo list, [qty, unit_cost] pairs
            fifo_lst = []
            t_qty = quantity
            for svl_in in svl_loc_in:
                if t_qty > svl_in.quantity:
                    fifo_lst.append([svl_in.quantity, svl_in.unit_cost, svl_in.value, svl_in.stock_move_id, svl_in])
                    t_qty -= svl_in.quantity
                else:
                    fifo_lst.append([t_qty, svl_in.unit_cost, svl_in.value, svl_in.stock_move_id, svl_in])
                    break
            # assign unit cost to delivery svls based on fifo_lst
            print(svl_loc_out)
            print(fifo_lst)
            
            if fifo_lst:
                last_price = fifo_lst[0][1]
                for svl_out in svl_loc_out:
                    svls_recreate_account_move.append(svl_out)
                    if svl_out.valued_type == 'reception_return':
                        for i in range(len(fifo_lst)):
                            fifo_entry = fifo_lst[i]
                            if fifo_entry[3] in svl_out.stock_move_id.move_orig_ids:
                                fifo_entry[0] -= abs(svl_out.quantity)
                                if svl_out.unit_cost != fifo_entry[1]:
                                    # fix reception_return unit_cost and value
                                    svl_out.unit_cost = fifo_entry[1]
                                    svl_out.value = fifo_entry[1] * svl_out.quantity
                                if fifo_entry[0] == 0:
                                    del fifo_lst[i]
                                break
                    else:
                        svl_qty = abs(svl_out.quantity)
                        if not fifo_lst:
                            svl_out.unit_cost = last_price
                            svl_out.value = svl_out.quantity * last_price
                        else:
                            fifo_qty = fifo_lst[0][0]
                            if svl_qty <= fifo_qty:
                                last_price = fifo_lst[0][1]
                                svl_out.unit_cost = last_price
                                svl_out.value = (-1) * svl_qty * svl_out.unit_cost
                                fifo_lst[0][0] = fifo_qty - svl_qty
                                if fifo_lst[0][0] == 0:
                                    fifo_lst.pop(0)
                            else:
                                value = 0
                                while svl_qty > 0:
                                    if fifo_lst:
                                        [fifo_qty, unit_cost, val, mv, svl_id] = fifo_lst[0]
                                        last_price = unit_cost
                                        if fifo_qty <= svl_qty:
                                            value += fifo_qty * unit_cost
                                            svl_qty -= fifo_qty
                                            fifo_lst.pop(0)
                                        else:
                                            value += svl_qty * unit_cost
                                            fifo_lst[0][0] = fifo_qty - svl_qty
                                            break
                                    else:
                                        break
                                svl_out.value =(-1) * value
                                svl_out.unit_cost = (-1) * value / svl_out.quantity
                        # check for delivery_return in fifo_lst to have the correct value and unit_price
                        if svl_out.stock_move_id.move_dest_ids and svl_out.stock_move_id.move_dest_ids[0].state == 'done':
                            should_restart_fifo = True
                            for i in range(len(fifo_lst)):
                                fifo_entry = fifo_lst[i]
                                if fifo_entry[3] in svl_out.stock_move_id.move_dest_ids:
                                    # import ipdb; ipdb.set_trace(context=10)
                                    # fix new unit_price in fifo
                                    svl_out_uc = abs(svl_out.value / svl_out.quantity)
                                    if svl_out_uc != fifo_entry[1]:
                                        # fix reception_return unit_cost and value
                                        fifo_entry[1] = fifo_entry[4].unit_cost = svl_out_uc
                                        fifo_entry[4].value = svl_out_uc * fifo_entry[4].quantity
                                        svls_recreate_account_move.append(fifo_entry[4])
                                    break
                        # Fix internal transfer price
                        if svl_out.valued_type == "internal_transfer":
                            other_svl = svl_out.stock_move_id.stock_valuation_layer_ids.filtered(
                                lambda svl: svl.id != svl_out.id and svl.quantity > 0
                            )
                            if other_svl:
                                other_svl.unit_cost = svl_out.unit_cost
                                other_svl.value = other_svl.quantity * svl_out.unit_cost
                                svls_recreate_account_move.append(other_svl)
                        if should_restart_fifo:
                            svl_ret = self.env['stock.valuation.layer'].search(
                                [('stock_move_id', 'in', svl_out.stock_move_id.move_dest_ids.ids)], order="id asc")
                            if svl_ret:
                                svl_ret = svl_ret[0]
                                if round(abs(svl_ret.unit_cost - svl_out.unit_cost), 2) == 0:
                                    should_restart_fifo = False
                                else:
                                    svl_ret.unit_cost = svl_out.unit_cost
                                    svl_ret.value = svl_out.unit_cost * svl_ret.quantity
                                    svls_recreate_account_move.append(svl_ret)                                    
                                    break

    def _fix_remaining_qty_value(self):
        if self.product_id:
            products = self.product_id
        else:
            products = self.product_id or self.env['product.product'].search([])        
            
        # Fix remaining qty
        for quant in self.env['stock.quant'].search([('product_id', 'in', products.ids)]):
            if quant.location_id.usage == "internal":
                svls = self.env['stock.valuation.layer'].search(
                    [("product_id", "=", quant.product_id.id),
                     ("location_dest_id", "=", quant.location_id.id),
                     ("quantity", ">", 0)])
                qty = quant.quantity
                for svl in svls.sorted("create_date", reverse=True):
                    if qty > 0:
                        added_cost = 0
                        linked_svl = self.env['stock.valuation.layer'].search([('stock_valuation_layer_id', '=', svl.id)])
                        if linked_svl:
                            added_cost = sum(linked_svl.mapped('value'))
                        if svl.quantity <= qty:
                            svl.remaining_qty = svl.quantity
                            svl.remaining_value = svl.quantity * svl.unit_cost + added_cost
                            qty -= svl.quantity
                        else:
                            svl.remaining_qty = qty
                            svl.remaining_value = qty * svl.unit_cost + (qty/svl.quantity)*added_cost
                            qty = 0
        self.env.cr.commit()

    def _finalize_svls(self):
        #switch new_unit_cost vs unit_cost
        # and new_value vs value
        if self.product_id:
            products = self.product_id
        else:
            products = self.product_id or self.env['product.product'].search([])        

        locations = self.location_ids.mapped('location_id')        
        domain = ['&', 
                    ('product_id', 'in', products.ids), 
                    '|',
                        ('location_dest_id', 'in', locations.ids), 
                        ('location_id', "in", locations.ids),
                ]


        svls = self.env['stock.valuation.layer'].search(domain)
        for svl in svls:
            new = svl.unit_cost
            svl.unit_cost = svl.new_unit_cost
            svl_new_unit_cost = new

            new = svl.value
            svl.value = svl.new_value
            svl.new_value = new

            new = svl.remaining_value
            svl.remaining_value = svl.new_remaining_value
            svl.new_remaining_value = new        

            new = svl.remaining_qty
            svl.remaining_qty = svl.new_remaining_qty
            svl.new_remaining_qty = new              