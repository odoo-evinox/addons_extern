{
    'name': 'Show on partner credit debit payments and unreconciled entries',
    'category': 'Accounting/Accounting',
    'version': '14.0.0.1',
    'author':'Nexterp Romania',
    'description': ''' Show on partner credit debit payments and unreconciled entries
    in tab invoicing, show existing partner fields  debit, credit, has_unreconciled_entries
    
    addend also total_bills
    
    and added total_payments 

''',
    'depends': ['account',
                'purchase', # only to put total_bills in same vendor bills button
                
                ],
    'data': [
        'views/res_partner.xml',
    ],
    

    'installable': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
