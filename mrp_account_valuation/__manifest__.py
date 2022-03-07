# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Accounting - MRP Unbuild Valuation',
    'version': '14.0.1.0.1',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Analytic accounting in Manufacturing',
    'description': """
    Show Valuation Button in Unbuild Orders
""",
    'website': 'https://nexterp.ro',
    'depends': ['mrp_account'],
    "init_xml" : [],
    "demo_xml" : [],
    "data": [
        "views/mrp_unbuild_views.xml",
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
