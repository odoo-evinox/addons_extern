# Copyright 2020 NextERP Romania SRL
{
    "name": " Sale report invoice lines grouped per product",
    "version": "13.0.1.0.0.",
    "category": "Accounting",
    "summary": "Sale report - Report of invoice lines in period grouped per product",
    "author": "NextERP Romania",
    "website": "http://www.nexterp.ro",
    "depends": [
        "account",
        "date_range",
    ],
    "license": "AGPL-3",
    "data": [
         "wizard/invoice_lines_wizard.xml",
         "reports/invoice_lines_wizard_report.xml",
    ],
    "installable": True,
}
