from odoo import _, api, fields, models


class stock_location(models.Model):
    _inherit = "stock.location"
    user_id = fields.Many2one("res.users", string="Manager")
