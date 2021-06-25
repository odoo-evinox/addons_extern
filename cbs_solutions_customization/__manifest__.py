{
    "name": "CBS Solutions customization invoice format, payment format, print invoice and payment on same page",
    "summary": "CBS Solutions customization",
    "description": """
    - header and footer very simple
    - invoice has at top issuer data, invoice number+data.., client data 
    - cache payments can be print 2 on same page
    - if invoice is paied with only one cache receipt is posible to print the invoice and payment on same page
    """,
    "version": "14.0.1.0.2",
    "category": "Localization",
    "author": "NextERP",
    "website": "https://nexterp.ro",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["account",  "l10n_ro_account_report_invoice"],
    "data": [
        "data/report_paperformat_data.xml",
         "report/report_headers_templates.xml",
         "report/invoice_report.xml",

         "report/report_payment_receipt_templates.xml",
         
         "report/invoice_width_payment_receipt.xml",
    ],
}
