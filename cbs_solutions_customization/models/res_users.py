# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    signed_image = fields.Binary(string='Signature image', company_dependent=True)

