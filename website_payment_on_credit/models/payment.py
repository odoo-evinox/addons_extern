from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.float_utils import float_compare
import pprint

class OnCreditAcquirer(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(selection_add=[("on_credit", "On Credit")], ondelete={"on_credit": "set default"})

    def _get_feature_support(self):
        res = super()._get_feature_support()
        res["authorize"].append("on_credit")
        return res

    def on_credit_get_form_action_url(self):
        return "/payment/on_credit/feedback"



class OnCreditTransaction(models.Model):
    _inherit = "payment.transaction"

    state = fields.Selection(selection_add=[('on_credit', 'On_credit')],ondelete={"on_credit": "set default"} )

    def on_credit_s2s_void_transaction(self):
        self._set_transaction_cancel()

    def on_credit_s2s_capture_transaction(self):
        self._set_transaction_done()
        tx_to_process = self.filtered(lambda x: x.state == "done" and x.is_processed is False)
        tx_to_process._post_process_after_done()


    @api.model
    def _on_credit_form_get_tx_from_data(self, data):
        reference, amount, currency_name = data.get('reference'), data.get('amount'), data.get('currency_name')
        tx = self.search([('reference', '=', reference)])

        if not tx or len(tx) > 1:
            error_msg = _('received data for reference %s') % (pprint.pformat(reference))
            if not tx:
                error_msg += _('; no order found')
            else:
                error_msg += _('; multiple order found')
            _logger.info(error_msg)
            raise ValidationError(error_msg)

        return tx

    def _on_credit_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if float_compare(float(data.get('amount') or '0.0'), self.amount, 2) != 0:
            invalid_parameters.append(('amount', data.get('amount'), '%.2f' % self.amount))
        if data.get('currency') != self.currency_id.name:
            invalid_parameters.append(('currency', data.get('currency'), self.currency_id.name))

        return invalid_parameters

    def _on_credit_form_validate(self, data):  # why is not getting here
        _logger.info('Validated on_credit payment for tx %s: set as pending' % (self.reference))

        if not self.acquirer_id.capture_manually:
            self._set_transaction_authorized()
        else:
            self._set_transaction_pending()
        return True

#        self._set_transaction_done()   # here is creating also the account_payment for bank, that is not ok.
        allowed_states = ('draft', 'authorized', 'pending', 'error')
        target_state = 'on_credit'
        (tx_to_process, tx_already_processed, tx_wrong_state) = self._filter_transaction_state(allowed_states, target_state)
        for tx in tx_already_processed:
            _logger.info('Trying to write the same state twice on tx (ref: %s, state: %s' % (tx.reference, tx.state))
        for tx in tx_wrong_state:
            _logger.warning('Processed tx with abnormal state (ref: %s, target state: %s, previous state %s, expected previous states: %s)' % (tx.reference, target_state, tx.state, allowed_states))

        tx_to_process.write({
            'state': target_state,
            'date': fields.Datetime.now(),
             # commented because is showing on /shop/confirmation as alert
             #           'state_message': 'This state means that the client will pay us later based on emitted invoices',
        })

        
        return True

        