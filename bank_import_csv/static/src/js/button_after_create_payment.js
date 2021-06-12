odoo.define('bank_import_csv.button_after_create_payment', function (require) {
"use strict";
var ListController = require('web.ListController');
var ListView = require('web.ListView');
var viewRegistry = require('web.view_registry');

var TransactionsListController = ListController.extend({ 
    buttons_template: 'BankImportCsv.buttons',    // the xml template name from /static/src/js/xm.  is using the var  ListView from higher
    
    events: _.extend({}, ListController.prototype.events, { 'click .js_import_bank_payment': '_import_bank_payment',    }),

    _import_bank_payment: function () {
           var self = this;
           this.do_action({
                name: "Import transactions",
                res_model: "account.payment.import.bank",
                views: [[false, "form"]],
                type: "ir.actions.act_window",
                view_mode: "form",
                target: "new",},
                {  on_close: function () { //alert('on_close');
                self.reload();}}
                
                        ); 
                                    },

})


var button_after_create_payment_ = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: TransactionsListController,
    }),
});

viewRegistry.add('button_after_create_payment', button_after_create_payment_);

});
