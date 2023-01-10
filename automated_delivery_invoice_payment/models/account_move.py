from odoo import fields, models
import time
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"
    
    paid_more = fields.Float(
            readonly=1, tracking=1,
            help='The positive difference between the online payment on sale_order'
                ' and the value of products that were invoices'
    )
    paid_less = fields.Float(
            readonly=1, tracking=1,
            help='The negative difference between the online payment on sale_order'
                ' and the value of products that were invoices'
    )
    difference_between_order_and_deliverd = fields.Boolean(
            readonly=1, tracking=1,
            help='This mean that was a difference between what was on the delivery'
            ' and what was really delivered and invoiced. If you have aso value in'
            ' payd less or more you must take action to see what to do with the money'
    )
    resolved_difference = fields.Char(
            tracking=1, help="If difference_between_order_and_deliverd, a text field"
            " to tell how you solved the situation"
    )
    