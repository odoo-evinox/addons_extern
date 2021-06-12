{
    'name': 'Import CSV Romania Banca Transilvania as payments',
    'category': 'Accounting/Accounting',
    'version': '14.0.0.1',
    'author':'Nexterp Romania',
    'description': ''' import banca transilvania csv format bank
    we are going to import the statement as  account.payments  and not as account.bank.statement.line
    the complexity of workig is 10 times bigger in having 2 models for payments instead of one with 2 more fields
    
    no more invoice in_payment, no more 2 recociliation, no more same info in pyament and bank account.bank.statement.line
    no more hiden menus for statements ..

''',
    'depends': ['account'],
    'data': [
        'wizard/account_payment_import_bank.xml',
        # 'views/button_after_create_payment.xml',
        'views/account_payment.xml',
        'views/assets.xml',
        'security/ir.model.access.csv',
    ],
    
    'qweb': [ "static/src/xml/button_after_create_payment.xml",],

    'installable': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
