from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.exceptions import UserError
import pprint
import werkzeug
import logging
_logger = logging.getLogger(__name__)


class WebsiteSalePaymentOnCredit(WebsiteSale):

    def _get_shop_payment_values(self, order, **kwargs):
        values = super(WebsiteSalePaymentOnCredit,self)._get_shop_payment_values(order, **kwargs)
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


class OnPaymentController(http.Controller):
    _accept_url = '/payment/on_credit/feedback'

    @http.route([
        '/payment/on_credit/feedback',
    ], type='http', auth='public', csrf=False)
    def transfer_form_feedback(self, **post):
        #_logger.info('Beginning form_feedback with post data %s', pprint.pformat(post))  # debug
        request.env['payment.transaction'].sudo().form_feedback(post, 'on_credit')
        return werkzeug.utils.redirect('/payment/process')