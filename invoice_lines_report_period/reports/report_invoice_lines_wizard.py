# Copyright 2020 NextERP Romania SRL

from odoo import api, models

class ReportInvoiceLinesWizardGiveMoveLines(models.AbstractModel):
    _name = 'report.invoice_lines_report_period.invoice_lines_html_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        out_invoices_in_period = self.env['account.move'].search([('state','=','posted'),
                                                                   ('type','in',['out_invoice','out_receipt']),
                                                                   #('move_id.reversal_move_id','=',False), # wasn't reversed 
                                                                    ])
        search_domain = [('date','>=',data['date_from']), 
                          ('date','<=',data['date_to']),
                          ('display_type', '=', False),
                          ('exclude_from_invoice_tab', '=', False),
                          ('move_id', 'in', out_invoices_in_period.ids)
                          ]
        filters = ""
        if data['product_ids'][0][2]:
            search_domain += [('product_id', 'in', data['product_ids'][0][2] )]
            products = self.env['product.product'].search([('id', 'in', data['product_ids'][0][2])])
            filters += "Only products: "+", ".join([p.name for p in products])
        account_move_line_ids = self.env['account.move.line'].search(search_domain, order="product_id, date asc")
        sorted_account_move_line_ids = account_move_line_ids.sorted(key=lambda x: str( x.product_id.name))
        docargs = {
            'docs': self,
            'filters':filters,
            'lines':sorted_account_move_line_ids,
        }
        return docargs

