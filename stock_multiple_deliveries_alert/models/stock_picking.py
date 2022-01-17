# Copyright 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import timedelta
class StockPicking(models.Model):
    _inherit = "stock.picking"

    other_unfinished_deliveries_ids = fields.One2many("stock.picking", compute="_get_same_day_deliveries", compute_sudo=1, help="In his moment ( before refresh) this deliveries are for same partner and are not done/caceled/draft")
    finished_deliveries_same_day_ids = fields.One2many("stock.picking", compute="_get_same_day_deliveries", compute_sudo=1, help="For this client, exist in this deliveries donein last 23 hours that have status done. You could send also this product with them")

# this is to check over the limit
    def return_parent_or_self(self,partner_id):
        partner_id.ensure_one()
        if partner_id.parent_id:
            return self.return_parent_or_self(partner_id.parent_id)
        else:
            return partner_id

#    @api.depends()#'state','date_done','picking_type_code','partner_id'
    def _get_same_day_deliveries(self):
        for rec in self:
            if rec.picking_type_code != 'outgoing' or not rec.partner_id:
                rec.other_unfinished_deliveries_ids = False
                rec.finished_deliveries_same_day_ids = False
            else:
                yesterday = fields.datetime.now() - timedelta(hours = 23)
                highest_partner = self.return_parent_or_self(rec.partner_id)
                highest_partner_addreses = self.env['res.partner'].search([('id','child_of',highest_partner.id)])
                rec.other_unfinished_deliveries_ids = self.env['stock.picking'].search([('picking_type_code','=','outgoing'),('id','!=',rec.id),
                                                               ('partner_id','in',highest_partner_addreses.ids),
                                                               ('state','not in',['draft','cancel','done'])])
                rec.finished_deliveries_same_day_ids = self.search([('picking_type_code','=','outgoing'),
                                                               ('partner_id','in',highest_partner_addreses.ids),
                                                               ('date_done','>',str(yesterday)),
                                                               ('state','=','done'),
                                                               ('id','!=',rec.id)     ])
                