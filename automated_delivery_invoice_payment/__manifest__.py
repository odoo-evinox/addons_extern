{
    'name': 'After delivery automated posted invoice, payment ',
    'category': 'Stock',
    'version': '14.0.0.1',
    'author':'Nexterp Romania',
    'description': ''' 
    simplifing the odoo flux less clicks more thinks automaticaly.
    utomated posted invoice, payment after delivery
    1. at picking, the button validate now is validating without backorder, another button exist for original validate with posibility of backorder
    2. from sale the craete invoice is creating a invoice ithout downpayment ..., another button for original behavior
''',
    'depends': ['stock',
                'sale',
                'barcodes',
                'payment', 
                
                ],
    'data': [
        'views/stock_picking.xml',
#        'views/sale_order.xml',
    ],
    

    'installable': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
