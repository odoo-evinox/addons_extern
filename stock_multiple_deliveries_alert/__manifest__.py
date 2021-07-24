# Copyright 2019 ForgeFlow S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock multiple deliveries alert",
    "summary": "This module is telling in picking if are more deliveries to same customer",
    "version": "14.0.0.2",
    "license": "AGPL-3",
    "description":""" used if you have for example online shop and the customer is creating multiple orders. to know at delivery to make only one packet 
    ( and with this info you can take whatever decision you want. without it you will make a lot of deliveries for same partner) 
 
 v 0.2  also in sale you have a field called unprocess_delivery_ids meaning that exist at least one stock.picking that is not in ['draft', 'done', 'cancel']
        you have some filed to tell you that exist other sales with unprocess_delivery_ids  or other that are processed and in less than 24h     
    
    
    """,
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "depends": ["sale_stock"],
    "data": ["views/stock_picking_views.xml",
             "views/sale_order_views.xml",
             ],
}
