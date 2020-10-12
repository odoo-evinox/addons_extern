from odoo import models
from .report_invoice_lines_wizard import  function_to_return_filters_and_invoice_lines

class ReportStockCardReportXlsx(models.AbstractModel): 
    _name = "report.invoice_lines_report_period.invoice_lines_xlxs"
    _description = "invoice lines report XLSX"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objects):
        filters, account_move_lines = function_to_return_filters_and_invoice_lines(self,data)
        self._define_formats(workbook)
        sheet = workbook.add_worksheet(f'{data["date_from"]} {data["date_to"]}')
        row = 0
        sheet.write(row, 0, f'Report:{data["date_from"]} {data["date_to"]}', self.format_left_bold)
        row += 1
        if filters:
            sheet.write(row, 0, f'{filters}', self.format_left_bold)
            row += 1
        row +=1
        # I can take from xml table the format .. but I'm replicating it here
        col =0
        for header in ["Nr", "Product", "Product code", "Client", "Invoice date", "Invoice nr.", "Price", "Currency", "Quantity", "Price no VAT", "VAT",]:
            sheet.write(row, col, header, self.format_left_bold)
            col += 1
        row +=1
        col = 0
        counter = 1
        for l in account_move_lines:
            if l.currency_id:
                currency = l.currency_id.name
            else:
                currency = l.company_id.currency_id.name
            for cell in [counter, l.product_id.name, l.product_id.default_code, l.partner_id.name, l.move_id.invoice_date, l.move_id.name, 
                         round(l.price_subtotal/l.quantity,2), #<!-- not price unit because we are taking into account also the discount-->
                         currency, 
                         l.quantity, 
                         round(l.price_subtotal, 2), 
                         round(l.price_total-l.price_subtotal,2)]: 
                sheet.write(row, col, cell)
                col +=1 
            counter += 1
            row+=1
            col = 0
