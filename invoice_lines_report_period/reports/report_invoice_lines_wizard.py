# Copyright 2020 NextERP Romania SRL

from odoo import api, models

class ParticularReport(models.AbstractModel):
    _name = 'report.invoice_lines_report_period.ceva_html_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        account_move_line_ids = self.env['account.move.line'].search([('date','>=',data['date_from']), 
                                                                      ('date','<=',data['date_to']),
                                                                      ('display_type', '=', False),
                                                                      ('exclude_from_invoice_tab', '=', False),
                                                                      ],order="product_id, date asc")
#         for x in account_move_line_ids:
#             print(f'{x.id}, {x.date}, {x.product_id}, {x.product_id.name}')
        sorted_account_move_line_ids = account_move_line_ids.sorted(key=lambda x: str( x.product_id.name))


        report = report_obj._get_report_from_name('module.report_name')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
            'lines':sorted_account_move_line_ids,
        }
        return docargs

