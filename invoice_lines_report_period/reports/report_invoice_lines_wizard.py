# Copyright 2020 NextERP Romania SRL

from odoo import api, models

class ReportInvoiceLinesWizardGiveMoveLines(models.AbstractModel):
    _name = 'report.invoice_lines_report_period.invoice_lines_html_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        account_move_line_ids = self.env['account.move.line'].search([('date','>=',data['date_from']), 
                                                                      ('date','<=',data['date_to']),
                                                                      ('display_type', '=', False),
                                                                      ('exclude_from_invoice_tab', '=', False),
                                                                      ],order="product_id, date asc")
        sorted_account_move_line_ids = account_move_line_ids.sorted(key=lambda x: str( x.product_id.name))
        docargs = {
            'docs': self,
            'lines':sorted_account_move_line_ids,
        }
        return docargs

