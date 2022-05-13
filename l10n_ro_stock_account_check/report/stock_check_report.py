# Copyright (C) 2021 Terrabit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.tools.misc import format_date

_logger = logging.getLogger(__name__)


class StockAccountingCheck(models.TransientModel):
    _name = "stock.accounting.check"
    _description = "StockAccountingCheck"

    # Filters fields, used for data computation

    account_id = fields.Many2one("account.account")
    location_id = fields.Many2one("stock.location", domain="[('usage','=','internal')]")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    date_from = fields.Date("Start Date", required=True, default=fields.Date.today)
    date_to = fields.Date("End Date", required=True, default=fields.Date.today)

    line_ids = fields.One2many("stock.accounting.check.line", "report_id")

    @api.model
    def default_get(self, fields_list):
        res = super(StockAccountingCheck, self).default_get(fields_list)
        today = fields.Date.context_today(self)
        today = fields.Date.from_string(today)

        from_date = today + relativedelta(day=1, months=0, days=0)
        to_date = today + relativedelta(day=1, months=1, days=-1)

        res["date_from"] = fields.Date.to_string(from_date)
        res["date_to"] = fields.Date.to_string(to_date)
        return res

    def do_compute_product(self):
        self.line_ids.unlink()

        query = """
        select %(report)s as report_id,
                svl_id as stock_valuation_layer_id,
                a.product_id as product_id,
                a.location_id as location_id,
                a.location_dest_id as location_dest_id,
                a.account_id as account_id,
                svl_qty as qty_svl,
                a.unit_cost as svl_unit_cost,
                svl_value as amount_svl,
                case when type='factura' then svl_inv_qty else svl_am_qty end as qty_aml,
                case when type='factura' then svl_inv_value else svl_am_value end  as amount_aml
            from (
                select svl.id as svl_id, svl.product_id, svl.location_id, svl.location_dest_id, svl.account_id,
                    round(svl.quantity,6) svl_qty, svl.unit_cost, round(svl.value,6) svl_value,
                    case when aml.quantity!=0 then
                                case  when svl.quantity>0 then (round(svl.quantity,6)-aml.quantity)
                                        else (round(svl.quantity,6)+ aml.quantity) end
                            else 0 end as svl_inv_qty,
                    case when aml.amount_currency!=0  then
                                case when svl.quantity>0 then round(svl.value,6)-aml.amount_currency
                                        else round(svl.value,6)-aml.amount_currency  end
                        else 0 end as svl_inv_value,
                    case when COALESCE(am.quantity,amm.quantity)!=0 then
                            case  when svl.quantity>0 and COALESCE(am.quantity, amm.quantity)>0
                                        then round(svl.quantity,6)-COALESCE(am.quantity,amm.quantity)
                                    when svl.quantity>0 and COALESCE(am.quantity, amm.quantity)<0
                                        then round(svl.quantity,6)+COALESCE(am.quantity,amm.quantity)
                                    when svl.quantity<0 and COALESCE(am.quantity, amm.quantity)<0
                                        then round(svl.quantity,6)-COALESCE(am.quantity,amm.quantity)
                                    else round(svl.quantity,6)+COALESCE(am.quantity,amm.quantity) end
                            else 0 end as  svl_am_qty,
                    case when COALESCE(am.amount_currency, amm.amount_currency)!=0  then
                            case when svl.value>0 and COALESCE(am.amount_currency, amm.amount_currency)>0
                                        then round(svl.value,6)-COALESCE(am.amount_currency, amm.amount_currency)
                                    when svl.quantity>0 and COALESCE(am.amount_currency, amm.amount_currency)<0
                                        then round(svl.value,6)+COALESCE(am.amount_currency,amm.amount_currency)
                                    when svl.quantity<0 and COALESCE(am.amount_currency, amm.amount_currency)<0
                                        then round(svl.value,6)-COALESCE(am.amount_currency,amm.amount_currency)
                                    else round(svl.value,6)-COALESCE(am.amount_currency, amm.amount_currency)   end
                            else 0 end as svl_am_value,
                    case when svl.invoice_line_id!=NULL and svl.account_move_id=NULL
                            then 'factura' else 'iesire' end as type

                from stock_valuation_layer svl
                left join account_move_line aml on aml.id=svl.invoice_line_id
                left join (select aml.product_id, aml.quantity, aml.amount_currency, am.amount_total, am.id as am, aml.id as aml
                           from account_move_line aml, account_move am
                           where aml.move_id=am.id and aml.amount_currency<0 )
                    am on am.am=svl.account_move_id and aml.product_id=svl.product_id  and svl.quantity<0
                left join (select aml.product_id, aml.quantity, aml.amount_currency, am.amount_total, am.id as am, aml.id as aml
                          from account_move_line aml, account_move am
                           where aml.move_id=am.id and aml.amount_currency>0 )
                    amm on amm.am=svl.account_move_id and amm.product_id=svl.product_id and svl.quantity>0
                where svl.create_date between %(date_from)s  and %(date_to)s and svl.company_id=%(company)s
            ) a
        """
        params = {
            "report": self.id,
            "company": self.company_id.id,
            "date_from": fields.Date.to_string(self.date_from),
            "date_to": fields.Date.to_string(self.date_to),
        }
        if self.account_id.id:
            query += (" where a.account_id = %s" % self.account_id.id)
        if self.location_id.id:
            if self.account_id.id:
                query += (" and (a.location_id = %s or a.location_dest_id = %s)"
                          % (self.location_id.id, self.location_id.id))
            else:
                query += (" where (a.location_id = %s or a.location_dest_id = %s)"
                          % (self.location_id.id, self.location_id.id))
        self.env.cr.execute(query, params=params)
        lines = self.env.cr.dictfetchall()
        self.line_ids.create(lines)

    def button_show_report(self):
        self.do_compute_product()

        action = self.env["ir.actions.actions"]._for_xml_id(
            "l10n_ro_stock_account_check.action_stock_accounting_check_line"
        )
        action["display_name"] = "{} ({}-{})".format(
            action["name"],
            format_date(self.env, self.date_from),
            format_date(self.env, self.date_to),
        )
        return action


class StockAccountingCheckLine(models.TransientModel):
    _name = "stock.accounting.check.line"
    _description = "StockAccountingCheckLine"
    _order = "report_id"

    report_id = fields.Many2one("stock.accounting.check")
    stock_valuation_layer_id = fields.Many2one("stock.valuation.layer")
    product_id = fields.Many2one("product.product", string="Product")
    location_id = fields.Many2one("stock.location", string="Source")
    location_dest_id = fields.Many2one("stock.location", string="Destionation")
    account_id = fields.Many2one("account.account", string="Account")

    qty_svl = fields.Float(digits="Product Unit of Measure", string="Quantity SVL")
    svl_unit_cost = fields.Monetary(currency_field="currency_id", string="Unit Cost SVL")
    amount_svl = fields.Monetary(currency_field="currency_id", string="Amount SVL")

    qty_aml = fields.Float(digits="Product Unit of Measure", string="Diff Quantity")
    amount_aml = fields.Monetary(currency_field="currency_id", string="Diff Amount")

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    def get_general_buttons(self):
        return []
