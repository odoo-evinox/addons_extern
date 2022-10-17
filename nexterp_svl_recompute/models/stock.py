# Copyright (C) 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).


from odoo import api, fields, models
from odoo.tools import float_is_zero

import logging
_logger = logging.getLogger(__name__)


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    new_unit_cost = fields.Monetary('New Unit Value', readonly=True)
    new_value = fields.Monetary('New Total Value', readonly=True)
    new_remaining_qty = fields.Float(digits=0, readonly=True)
    new_remaining_value = fields.Monetary('New Remaining Value', readonly=True)
