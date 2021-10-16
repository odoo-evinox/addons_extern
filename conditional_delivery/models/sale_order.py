from odoo import fields, models, api,  SUPERUSER_ID
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.safe_eval import safe_eval

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_delivery_methods(self):
        # searching on website_published will also search for available website (_search method on computed field)
        address = self.partner_shipping_id
        original_carriers = self.env['delivery.carrier'].sudo().search([('website_published', '=', True)]).available_carriers(address)
        carriers_with_ok_domain = self.env['delivery.carrier']


        for carrier in original_carriers:
            if carrier.partner_domain:
                try:
                    ok_address = address.search([('id','=',address.id)]+safe_eval(carrier.partner_domain))
                    if not ok_address:
                        continue  # we are excluding this carrier address
                except Exception as ex:
                    _logger.error(f'at carrier ({carrier},carrier.name) partner_domain={carrier.partner_domain} gives error: {ex}')
            carriers_with_ok_domain |= carrier

        return carriers_with_ok_domain

