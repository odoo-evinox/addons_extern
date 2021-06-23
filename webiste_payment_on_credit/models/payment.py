from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.float_utils import float_compare
import pprint

class OnDeliveryAcquirer(models.Model):
    _inherit = "payment.acquirer"

    provider = fields.Selection(selection_add=[("on_credit", "On Credit")], ondelete={"on_credit": "set default"})

    def _get_feature_support(self):
        res = super()._get_feature_support()
        res["authorize"].append("on_credit")
        return res

    def on_credit_get_form_action_url(self):
        return "/payment/on_credit/feedback"

    def _format_on_credit_data(self):
        company_id = self.env.company.id
        # filter only bank accounts marked as visible
        journals = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', company_id)])
        accounts = journals.mapped('bank_account_id').name_get()
        bank_title = _('Bank Accounts') if len(accounts) > 1 else _('Bank Account')
        bank_accounts = ''.join(['<ul>'] + ['<li>%s</li>' % name for id, name in accounts] + ['</ul>'])
        post_msg = _('''<div>
<h3>Your order was validated, with the payment on credit. Please pay them in term, to the following bank account</h3>
<h4>%(bank_title)s</h4>
%(bank_accounts)s
<h4>Communication</h4>
<p>Please use the order name as communication reference.</p>
</div>''') % {
            'bank_title': bank_title,
            'bank_accounts': bank_accounts,
        }
        return post_msg

    @api.model
    def create(self, values):
        """ Hook in create to create a default pending_msg. This is done in create
        to have access to the name and other creation values. If no pending_msg
        or a void pending_msg is given at creation, generate a default one. """
        if values.get('provider') == 'on_credit' and not values.get('pending_msg'):
            values['pending_msg'] = self._format_on_credit_data()
        return super().create(values)

    def write(self, values):
        """ Hook in write to create a default pending_msg. See create(). """
        if not values.get('pending_msg', False) and all(not acquirer.pending_msg and acquirer.provider != 'on_credit' for acquirer in self) and values.get('provider') == 'on_credit':
            values['pending_msg'] = self._format_on_credit_data()
        return super().write(values)


class OnDeliveryTransaction(models.Model):
    _inherit = "payment.transaction"


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
        self._set_transaction_authorized() 
        return True

        