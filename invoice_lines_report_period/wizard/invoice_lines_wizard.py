# Copyright 2020 NextERP Romania SRL

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class InvoiceLinesWizard(models.TransientModel):
    _name = "invoice.lines.wizard"
    _description = "invoice.lines.wizard for generating report"

    date_range_id = fields.Many2one(comodel_name="date.range", string="Period")
    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")
    product_ids = fields.Many2many(comodel_name="product.product", string="Show only this products")

    @api.onchange("date_range_id")
    def _onchange_date_range_id(self):
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

