# Copyright 2020 NextERP Romania SRL

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from datetime import date, timedelta

class InvoiceLinesWizard(models.TransientModel):
    _name = "invoice.lines.wizard"
    _description = "invoice.lines.wizard for generating report"

    def get_last_month_dates(self, first=True):
        this_month_first_day = date.today().replace(day=1)
        last_month_last_day = this_month_first_day - timedelta(days=1)
        last_month_fist_day = last_month_last_day.replace(day=1)
        if first:
            return last_month_fist_day
        else:
            return last_month_last_day

    def get_last_month_last_day(self):
        return self.get_last_month_dates(False)
        
    date_range_id = fields.Many2one(comodel_name="date.range", string="Period")
    date_from = fields.Date(string="Start Date",default=get_last_month_dates)
    date_to = fields.Date(string="End Date",default=get_last_month_last_day)
    product_ids = fields.Many2many(comodel_name="product.product", string="Show only this products")

    @api.onchange("date_range_id")
    def _onchange_date_range_id(self):
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    def button_export_html(self):
        self.ensure_one()
        data = self._prepare_invoice_lines_report()
        return self.env.ref('invoice_lines_report_period.print_report_html').report_action(self, data=data)

    def button_export_pdf(self):
        self.ensure_one()
        data = self._prepare_invoice_lines_report()
        return self.env.ref('invoice_lines_report_period.print_report_pdf').report_action(self, data=data)
 
    def button_export_xlsx(self):
        self.ensure_one()
        data = self._prepare_invoice_lines_report()
        return self.env.ref('invoice_lines_report_period.print_report_xlsx').report_action(self, data=data)

    def _prepare_invoice_lines_report(self):
        self.ensure_one()
        return {
            "date_from": self.date_from,
            "date_to": self.date_to or fields.Date.context_today(self),
            "product_ids": [(6, 0, self.product_ids.ids)],
        }

