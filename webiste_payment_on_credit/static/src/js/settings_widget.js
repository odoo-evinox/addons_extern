odoo.define('automated_delivery_invoice_payment.SettingsWidget', function (require) {
'use strict';

var orginalSettingsWidget = require('stock_barcode.SettingsWidget');

orginalSettingsWidget.prototype.events = _.extend({}, orginalSettingsWidget.prototype.events, {
         'click .o_print_created_invoice': '_onClickPrintCreatedInvoice'
    });

orginalSettingsWidget.include({

      _onClickPrintCreatedInvoice: function (ev) {
           ev.stopPropagation();
           this.trigger_up('picking_print_createdinvoice');
        },
 
});

});

// print picking action
odoo.define('automated_delivery_invoice_payment.picking_client_action_me', function (require) {
'use strict';


var originalClientAction = require('stock_barcode.picking_client_action');

originalClientAction.prototype.custom_events = _.extend({}, originalClientAction.prototype.custom_events, {
         'picking_print_createdinvoice': '_onPrintingInvoice'
    });


originalClientAction.include({

      _onPrintingInvoice: function (ev) {
        ev.stopPropagation();
        this._printInvoice();
        },

    _printInvoice: function () {
        var self = this;
        this.mutex.exec(function () {
            return self._save().then(function () {
                return self._rpc({
                    'model': 'stock.picking',
                    'method': 'print_created_invoice',
                    'args': [[self.actionParams.id]],
                }).then(function(res) {
                    return self.do_action(res);
                });
            });
        });
                        },
 
});


});
