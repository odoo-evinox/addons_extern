# Copyright 2019 ForgeFlow S.L.
# Copyright 2019 Aleph Objects, Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Stock multiple deliveries alert",
    "summary": "This module is telling in picking if are more deliveries to same customer",
    "version": "14.0.0.1",
    "license": "AGPL-3",
    "description":""" used if you have for example online shop and the customer is creating multiple orders. to know at delivery to make only one packet 
    ( and with this info you can take whatever decition you want. without it you will make a lot of deliveries for same partner) """,
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "depends": ["stock"],
    "data": ["views/stock_picking_view.xml"],
}
