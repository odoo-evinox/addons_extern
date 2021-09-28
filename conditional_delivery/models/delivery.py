from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    partner_domain = fields.Char(default="", tracking=1, help="If this field is set, will display the current currier only at res_partners (contacts) that met the domain condition ( example with a field for a special module [('b2b','=','b2b')]  ) . If the domain has errors will not be like no domain ")

