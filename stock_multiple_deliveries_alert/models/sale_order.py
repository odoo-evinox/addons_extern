# Copyright 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from datetime import timedelta
class SaleOrder(models.Model):
    _inherit = "sale.order"

    has_unprocess_delivery = fields.Boolean(store=1,copy=0,index=1, compute="_get_unprocess_delivery_ids", compute_sudo=1, help="In his moment ( before refresh) exist pickings for this sale_order that are not in ['draft', 'done', 'cancel'] state")

    other_unprocess_sales_ids = fields.One2many("sale.order", compute="_get_other_sales", compute_sudo=1, help="In his moment ( before refresh) exist other sale_orders that have unprocessed deliveries")
    finished_sales_same_day_ids = fields.One2many("sale.order", compute="_get_other_sales", compute_sudo=1, help="For this client, exist other not draft/cancel sale_orders in same day")

    @api.depends('picking_ids','picking_ids.state')
    def _get_unprocess_delivery_ids(self):
        for rec in self:
            if rec.state == 'cancel':
                rec.has_unprocess_delivery = False
            else:
                rec.has_unprocess_delivery = rec.picking_ids.filtered(lambda r: r.state not in ['draft','cancel','done']) or False
# this is to check over the limit
    def return_parent_or_self(self,partner_id):
        partner_id.ensure_one()
        if partner_id.parent_id:
            return self.return_parent_or_self(partner_id.parent_id)
        else:
            return partner_id    

    def _get_other_sales(self):
        for rec in self:
            yesterday = fields.datetime.now() - timedelta(hours = 23)
            highest_partner = self.return_parent_or_self(rec.partner_id)
            highest_partner_addreses = self.env['res.partner'].search([('id','child_of',highest_partner.id)])
            rec.other_unprocess_sales_ids = self.search([      ('partner_id','in',highest_partner_addreses.ids),
                                                               ('state','not in',['draft','cancel']),
                                                               ('id','!=',rec.id),
                                                               ('has_unprocess_delivery','!=',False)])
            rec.finished_sales_same_day_ids = self.search([
                                                               ('partner_id','in',highest_partner_addreses.ids),
                                                               ('date_order','>',str(yesterday)),
                                                               ('id','!=',rec.id),
                                                               ('state','not in',['draft'',cancel'])])
                    
    
    
                