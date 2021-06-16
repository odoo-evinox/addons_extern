{
    'name': 'After delivery automated posted invoice, payment ',
    'category': 'Stock',
    'version': '14.0.0.1',
    'author':'Nexterp Romania',
    'description': ''' 
    simplifing the odoo flux less clicks more thinks automaticaly.
    utomated posted invoice, payment after delivery
    1. at picking, the button validate now is validating without backorder, another button exist for original validate with posibility of backorder
    2. at validate the transfer is calling the button 'create invoice' from sale_order  that creating a invoice without downpayment and is validating it
    3  the resulting invoice from step2 is stored in picking in field created_invoice_id (visible in tab Aditional Info) and exist posibility to print it
    4. the print of invoice exist also on barcode interface
''',
    'depends': ['stock',
                'sale',
                'barcodes',
                'payment', 
                'stock_barcode', # just to show print invoice in stock_barcode application 
                'delivery',
                'cbs_solutions_customization', # for format of invoice with payment
                ],
    'data': [
        'views/stock_picking.xml',
        'views/assets.xml',
        'views/sale_order.xml',
    ],
    'qweb': [
        "static/src/xml/qweb_templates.xml", # just to show print invoice in stock_barcode application
    ],    

    'installable': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
