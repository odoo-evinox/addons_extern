from odoo import models, fields, api, _


class stock_picking(models.Model):
    _inherit = ['stock.picking','comment.template']
    _name = 'stock.picking'

    purchase_id = fields.Many2one('purchase.order',readonly=1,string="Created by this purchase")  

    
    delegate_id = fields.Many2one('res.partner', string='Delegate')
    mean_transp = fields.Char(string='Mean transport')

    installed_stock_picking_report_valued = fields.Boolean(compute="_compute_installed_stock_picking_report_valued", compute_sudo=True,store=True)

    show_shop_price = fields.Boolean(compute="_compute_show_shop_price", compute_sudo=True,store=True)

    def _compute_installed_stock_picking_report_valued(self):
        stock_piging_report_valued = self.env['ir.module.module'].search([('name','=','stock_picking_report_valued')])
        if stock_piging_report_valued.filtered(lambda r: r.state == 'installed'):
            self.write({'show_shop_price':True})
        else:
            self.write({'show_shop_price':False})

    @api.depends('installed_stock_picking_report_valued')
    def _compute_show_shop_price(self):
        for record in self:
            if record.purchase_id and record.location_dest_id.merchandise_type=='shop' :
                record.show_shop_price = True
                continue
            record.show_shop_price = False

    @api.onchange('delegate_id')
    def on_change_delegate_id(self):
        if self.delegate_id :
            self.mean_transp = self.delegate_id.mean_transp

    def write(self, vals):
        "if modified the mean_transp will write into delegate"
        mean_transp = vals.get('mean_transp',False)
        delegate_id = vals.get('delegate_id',False)
        if mean_transp and delegate_id:
            if mean_transp!= self.env['res.partner'].sudo().browse(delegate_id).mean_transp:
                self.env['res.partner'].sudo().browse(delegate_id).write({'mean_transp':mean_transp})
        return super().write(vals)



