from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class WebsiteSalePaymentOnCredit(WebsiteSale):

    def _get_shop_payment_values(self, order, **kwargs):
        values = super()._get_shop_payment_values(order, **kwargs)
        parent_or_self = order.partner_id.return_parent_or_self()
        on_credit_acquiers = []
        values['on_credit_acquiers_reason'] = {}
        not_on_credit_acq = []
        for acquier in  values['acquirers']:
            values['on_credit_acquiers_reason'][acquier] = ''
            if acquier.provider == 'on_credit':
                on_credit_acquiers += acquier
            else:
                not_on_credit_acq += acquier

        if parent_or_self.credit_limit:
            try:
                parent_or_self.check_over_credit_limit(order.amount_total)
            except Exception as ex:
                for acq in on_credit_acquiers:
                    values['on_credit_acquiers_reason'][acq] = ex
        else: # partner does not have credit_limit so we are not going to show payment acquier type on_credit
            values['acquirers']  = not_on_credit_acq
        return values
