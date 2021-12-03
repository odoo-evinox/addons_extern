{
    "name": "CBS Solutions customization report invoice format, payment format, print invoice and payment on same page",
    "summary": "CBS Solutions customization",
    "description": """
    - header and footer very simple
    - invoice has at top issuer data, invoice number+data.., client data 
    - cache payments can be print 2 on same page
    -  will show on print also the account_payments that are with cash
    - on invoice showing in another tab also the payments made from bank/cash ( account_payments)


used at simple accounting by cbs ( no enterprise module)

v0.4  now even if in sale_order we have show discount ( and in account_move_line we have price and discount) 
on invoice to be easy for the client we put the price with discount ( and not big price and discount)
v0.5 for v0.4 you need to uncomment /comment in invoice_report_xml


    """,
    "version": "14.0.1.0.4",
    "category": "Localization",
    "author": "NextERP",
    "website": "https://nexterp.ro",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["account",  "l10n_ro_account_report_invoice"],
    "data": [
        "data/report_paperformat_data.xml",
         "views/account_move_view.xml",
         
         "report/report_headers_templates.xml",
         "report/invoice_report.xml",

         "report/report_payment_receipt_templates.xml",
         
    ],
}
