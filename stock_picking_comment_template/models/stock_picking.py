from odoo import models, fields, api, _


class stock_picking(models.Model):
    _inherit = ['stock.picking', 'comment.template']
    _name = 'stock.picking'
    
