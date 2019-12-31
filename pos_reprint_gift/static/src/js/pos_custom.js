odoo.define('pos_reprint_gift.pos_reprint_gift', function (require) {
"use strict";

var devices = require('point_of_sale.devices');
var screens = require('point_of_sale.screens');
var core = require('web.core');
var QWeb = core.qweb;

var _t = core._t;

screens.ReceiptScreenWidget.include({
    events : {
        "click .Print-Gift-Receipt" : "print_gift",
    },
    print_gift: function() {
        this.$('.pos-sale-ticket').replaceWith(QWeb.render('PosTicketGift', this.get_receipt_render_env()));
        this.print_web();
        this.$('.pos-sale-ticket').replaceWith(QWeb.render('PosTicket', this.get_receipt_render_env()));
    },
});

//devices.ProxyDevice.include({
//    print_receipt: function(receipt) {
//        this._super(receipt);
//        this.pos.old_receipt = receipt || this.pos.old_receipt;
//    },
//});
//
//var ReprintButton = screens.ScreenWidget.extend({
//    template: 'ReprintButton',
//    events : {
//        "click .Print-Gift-Receipt" : "button_click",
//    },
//    button_click: function() {
//        console.log('clicked');
//        if (this.pos.old_receipt) {
//            this.pos.proxy.print_receipt(this.pos.old_receipt);
//        } else {
//            this.gui.show_popup('error', {
//                'title': _t('Nothing to Print'),
//                'body':  _t('There is no previous receipt to print.'),
//            });
//        }
//    },
//});
//screens.define_action_button({
//    'name': 'reprint',
//    'widget': ReprintButton,
//    'condition': function(){
//        return this.pos.config.iface_reprint && this.pos.config.iface_print_via_proxy;
//    },
//});

});

