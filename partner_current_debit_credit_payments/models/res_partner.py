from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    payment_ids = fields.One2many('account.payment', 'partner_id', string='Payments', readonly=True, copy=False)
    total_payments = fields.Monetary(compute='_payment_total', string="Total Payment",
        groups='account.group_account_invoice,account.group_account_readonly')
    total_bills = fields.Monetary(compute='_bills_total', string="Total Bills",
        groups='account.group_account_invoice,account.group_account_readonly')

    def _payment_total(self):
        self.total_payments = 0
        if not self.ids:
            return True

        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self.filtered('id'):
            # price_total is in the company currency
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]

        domain = [
            ('partner_id', 'in', all_partner_ids),
            ('state', 'not in', ['draft', 'cancel']),        ]
        totals = self.env['account.payment'].read_group(domain, ['amount'], ['payment_type'])
        for partner, child_ids in all_partners_and_children.items():
            partner.total_payments = sum(x['amount']*(1 if x['amount']=='inbound' else (-1)) for x in totals )

    def action_view_partner_payments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments")
        action['domain'] = [
           # ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('partner_id', 'child_of', self.id),
        ]
        action['context'] = {}
        return action    

    def _bills_total(self):
        self.total_bills = 0
        if not self.ids:
            return True

        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self.filtered('id'):
            # price_total is in the company currency
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]

        domain = [
            ('partner_id', 'in', all_partner_ids),
            ('state', 'not in', ['draft', 'cancel']),
            ('move_type', 'in', ('in_invoice', 'in_refund')),
        ]
        price_totals = self.env['account.invoice.report'].search(domain)  
        for partner, child_ids in all_partners_and_children.items():
            partner.total_bills = sum(x.move_id.amount_total for x in price_totals)
