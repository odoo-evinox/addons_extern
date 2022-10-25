# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from collections import defaultdict
from dateutil.relativedelta import relativedelta


_interval = {
    '15': lambda count: relativedelta(days=count*15),
    '30': lambda count: relativedelta(days=count*30)
}

NUMBER_INTERVALS = 5

class SVLAgeReportLocation(models.TransientModel):
    _name = 'l10n.ro.svl.age.report.location'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
    )
    report_id = fields.Many2one(
        'l10n.ro.svl.age.report',
        string='Report',
    )


class SVLAgeReport(models.TransientModel):
    _name = 'l10n.ro.svl.age.report'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    product_id = fields.Many2one('product.product', "Related product", check_company=True)
    date_ref = fields.Date("Reference Date", default=fields.Date.today)

    interval_days = fields.Selection(string="Days", selection=[('15', '15 days'), ('30', '30 days')], default="15")

    location_ids = fields.One2many(
        'l10n.ro.svl.age.report.location',
        'report_id',
        string='Locations',
        compute="_compute_location_ids",
        store=True
    )
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        required=True,
        string="Warehouse",
        readonly=False,
        help="Warehouse to consider for the route selection",
    )    
    line_ids = fields.One2many(
        'l10n.ro.svl.age.report.line',
        'report_id',
        string='Report Lines',
    )

    def name_get(self):
        res = []
        for rep in self:
            name = "Stock Age Report: {} (interval: {})".format(
                rep.date_ref, dict(self._fields["interval_days"].selection).get(rep.interval_days)
            )
            res.append((rep.id, name))
        return res

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id)], 
            limit=1
        )
        res['warehouse_id'] = warehouse.id
        return res

    @api.depends('warehouse_id')
    def _compute_location_ids(self):
        self.location_ids = [(6, 0, [])]

        locs = self.env['stock.location'].search([('usage', '=', 'internal')], order="id")
        locs = locs.filtered(lambda l: l.get_warehouse() == self.warehouse_id)
        location_ids = []
        idx = 10
        for loc in locs:
            location_ids.append((0, 0, {
                'sequence': idx, 'location_id': loc.id
            }))
            idx += 10
        self.location_ids = location_ids

    def do_compute_report(self):
        if self.product_id:
            products = self.product_id
        else:
            products = self.product_id or self.env['product.product'].search([])
        locations = self.location_ids.mapped('location_id')

        for product in products:
            self._run_aged_inventory(product, locations.ids)

        return True

    def _run_aged_inventory(self, product, locations):
        self = self.sudo()

        def _to_str(date):
            return fields.Date.to_string(date)

        date_ref = date_ref_next = fields.Date.from_string(self.date_ref)
        age_list = []
        days = 0
        for i in range(NUMBER_INTERVALS):
            date = date_ref - _interval[self.interval_days](i)
            age_list.append({
                'date': date, 
                'quantity': 0, 
                'value': 0, 
            }) 

            days_next = (date_ref - (date_ref - _interval[self.interval_days](i + 1))).days
            name = f'{days} - {days_next}'            
            if i == NUMBER_INTERVALS - 1:
                name += '+' 
            age_list[i]['name'] = f'[{i+1}] {name} ' + _('days')
            days = days_next

        product = product.with_context(to_date=date)        
        if product.quantity_svl > 0.01:
            quantity_svl = round(product.quantity_svl, 2)            
            value_svl = round(product.value_svl, 2)
            age_list[NUMBER_INTERVALS - 1]['quantity'] = max(0, quantity_svl)
            age_list[NUMBER_INTERVALS - 1]['value'] = max(0, value_svl)

        svl_date_from = _to_str(age_list[0]['date'])
        svl_date_to = _to_str(age_list[NUMBER_INTERVALS - 1]['date'])
        domain = ['&',  
                    '&',
                        ('product_id', '=', product.id), 
                        '&',
                            ('create_date', '<=', svl_date_from),
                            ('create_date', '>', svl_date_to),
                    '|',
                        '&',
                            ('location_dest_id', 'in', locations), 
                            ('quantity', '>', 0.001),
                        '&',
                            ('location_id', "in", locations),
                            ('quantity', '<', 0.001),
                ]

        svls = list(self.env['stock.valuation.layer'].search(domain).sorted(lambda svl: svl.create_date))

        account_id = product.categ_id.property_stock_valuation_account_id
        if svls:
            account_id = svls[0].l10n_ro_account_id

            # for interval_nb in [3, 2, 1, 0]
            for interval_nb in reversed(range(NUMBER_INTERVALS - 1)):
                remaining_qty = remaining_qty_inital = sum([item['quantity'] for item in age_list[interval_nb:]])
                remaining_val = remaining_value_inital = sum([item['value'] for item in age_list[interval_nb:]])

                period_date_from = age_list[interval_nb]['date']
                period_date_to = age_list[interval_nb + 1]['date']

                quantity_period = 0
                value_period = 0

                while svls:
                    svl = svls[0]
                    if svl.create_date.date() > period_date_from:
                        break

                    is_out = False
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
                        if svl.quantity > 0:
                            svl_val = sum([s.value for s in (svl + svl.stock_valuation_layer_ids)])                   
                            quantity_period += svl.quantity
                            value_period += svl_val
                        else:
                            is_out = True

                    if svl.stock_move_id._is_out() or is_out:
                        current_qty = quantity_period + remaining_qty
                        if current_qty == 0:
                            #move svl later, after a reception
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
                            svl_qty = abs(svl.quantity)
                            svl_val = abs(svl.value)
                            if remaining_qty <= svl_qty:
                                remaining_qty = 0
                                remaining_val = 0
                                svl_qty -= remaining_qty
                                svl_val -= remaining_val

                                quantity_period -= svl_qty
                                value_period -= svl_val
                            else:
                                remaining_qty = max(0, remaining_qty - svl_qty)
                                remaining_val = max(0, remaining_val - svl_val)

                    svls = svls[1:]

                age_list[interval_nb]['quantity'] = quantity_period
                age_list[interval_nb]['value'] = value_period

                #update qty and value for intervals afterwards
                diff_qty = remaining_qty_inital - remaining_qty
                diff_val = remaining_value_inital - remaining_val
                for item in reversed(age_list[interval_nb:]):
                    if diff_qty >= item['quantity']:
                        item['quantity'] = 0
                        item['value'] = 0
                        diff_qty -= item['quantity']
                        diff_val -= item['value']
                    else:
                        item['quantity'] -= diff_qty
                        item['value'] -= diff_val
                        diff_qty = 0
                        diff_val = 0
                        break

        #create report lines
        lines = []
        for period in age_list:
            vals = {
                'report_id': self.id,
                'name': period['name'],
                'date': _to_str(period['date']),
                'product_id': product.id,
                'account_id': account_id and account_id.id,
                'quantity': period['quantity'],
                'value': period['value']
            }
            self.env['l10n.ro.svl.age.report.line'].create(vals)

    def button_show_sheet(self):
        self.do_compute_report()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "l10n_ro_stock_age_report.action_sheet_age_report_line"
        )

        action["display_name"] = "{} {} ({})".format(
            action["name"],
            self.date_ref,
            self.interval_days
        )
        action["domain"] = [("report_id", "=", self.id)]
        action["target"] = "main"
        return action

class SVLAgeReportLine(models.TransientModel):
    _name = 'l10n.ro.svl.age.report.line'
    _order = 'date desc'

    report_id = fields.Many2one("l10n.ro.svl.age.report", readonly=True)
    name = fields.Char(string='Days Range', readonly=True)
    date = fields.Date(readonly=True)
    product_id = fields.Many2one("product.product", readonly=True)
    internal_reference = fields.Char(
        "Internal Reference", related="product_id.default_code", 
        stored=True,
        readonly=True)
    product_uom = fields.Many2one(
        "uom.uom", string="UM", related="product_id.uom_id", readonly=True,
        stored=True
    )
    account_id =fields.Many2one('account.account', readonly=True)
    quantity = fields.Float("Quantity", readonly=True)
    value = fields.Float("Value", readonly=True)


