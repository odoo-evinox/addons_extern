from odoo import fields, models
import time
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    paid_more = fields.Float(help='From this sale order, last created invoice. The positive difference between the online payment on sale_order and the value of products that were invoices',default=0)
    paid_less = fields.Float(help='From this sale order, last created invoice. The negative difference between the online payment on sale_order and the value of products that were invoices',default=0)
    difference_between_order_and_deliverd = fields.Boolean(help='From this sale order, last created invoice. This mean that was a difference between what was on the delivery and what was really delivered and invoiced. If you have aso value in payd less or more you must take action to see what to do with the money',default=0)
    