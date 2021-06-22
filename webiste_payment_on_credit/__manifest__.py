{
    'name': 'webiste payment on credit ',
    'category': 'Website',
    'version': '14.0.0.1',
    'author':'Nexterp Romania',
    'description': ''' 
    If the partner has Credit Limit at partner in Sale&Purcase Tab, can show payment_on_credit  option as payment method on site,
    For partners that do not have credit_limit is not showing this type of payment.
    If is over the limit will show a warning and the payment method can not be used (is disabled). 
    
    When this payment method is selected, the order will be validated automatically ( like at a online payment) 
''',
    'depends': ['payment',
                'website_sale',
                'partner_current_debit_credit_payments',  # to know when the partner is over credit limit  

                ],
    'data': [
        'views/payment.xml',
        'views/templates.xml',
     ],
    'installable': True,
    'auto_install': True,
    'license': 'AGPL-3',
}
