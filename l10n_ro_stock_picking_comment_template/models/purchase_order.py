# Copyright (C) 2021 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_picking(self):
        res_dict = super()._prepare_picking()
        res_dict["purchase_id"] = self.id
        return res_dict
