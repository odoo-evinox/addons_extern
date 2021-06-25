# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _get_advance_details2(self, line):
        produs = ""
        produs = produs + str(line.product_id.name)
        if self.advance_payment_method == 'percentage':
            amount = line.price_subtotal * self.amount / 100
            name = _("Down payment of %s%% %s") % (self.amount, produs)
        else:
            amount = self.fixed_amount
            name = _('Down Payment %s') % produs

        return amount, name

    def _prepare_invoice_values2(self, order, name, amount, so_line):
        res = []
        for line in order.order_line:
            if not line.is_downpayment:
                res.append((0, 0, {
                        'name': self._get_advance_details2(line)[1],
                        'price_unit': self._get_advance_details2(line)[0],
                        'quantity': 1.0,
                        'product_id': self.product_id.id,
                        'product_uom_id': line.product_uom.id,
                        'tax_ids': [(6, 0, line.tax_id.ids)],
                        'sale_line_ids': [(6, 0, [so_line.id])],
                        'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                        'analytic_account_id': order.analytic_account_id.id or False,
                    }))
        return res

    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
        res['invoice_line_ids'] = self._prepare_invoice_values2(order, name, amount, so_line)
        return res

    def _prepare_so_line(self, order, analytic_tag_ids, tax_ids, amount):
        res = super(SaleAdvancePaymentInv, self)._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
        res['sequence'] = 10 + len(order.order_line)
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self,sequence):
        res = super(SaleOrderLine, self)._prepare_invoice_line(sequence=sequence)
        if self.is_downpayment:   # is just a name and has display_type = line_section
            pass # why did I put this in here?
            #@res['quantity'] = -1
        return res