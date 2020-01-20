odoo.define('pos_lines_discount.discount_all.js',function(require) {
    "use strict";
var core = require('web.core');
var screens = require('point_of_sale.screens');

var _t = core._t;

  var core = require('web.core');
    var QWeb = core.qweb;
    var screens = require('point_of_sale.screens');
    var models = require('point_of_sale.models');
    var PopupWidget = require('point_of_sale.popups');
    var gui     = require('point_of_sale.gui');
    var NumpadWidget = screens.NumpadWidget;
    var Chrome = require('point_of_sale.chrome');
var PasswordInputPopupWidget = PopupWidget.extend({
    template: 'PasswordInputPopupWidget',
    show: function(options){
        options = options || {};
        this._super(options);

        this.renderElement();
        this.$('input,textarea').focus();
    },
    click_confirm: function(){
        var value = this.$('input,textarea').val();
        this.gui.close_popup();
        if( this.options.confirm ){
            this.options.confirm.call(this,value);
        }
    },
});

var DiscountButtonAll = screens.ActionButtonWidget.extend({
    template: 'DiscountButtonAll',

    button_click: function(){

     var self = this;
        var order    = this.pos.get_order();
        var lines    = order.get_orderlines();
        console.log('lines== ',lines);

        if (self.pos.config.lock_all_disc == true) {
                    self.gui.show_popup('passwordinput', {
                        'title': _t('passwordinput ?'),
                        confirm: function (pw) {
                        console.log('pw== ',pw);
                        console.log('all pw== ',self.pos.config);
                            if (pw !== self.pos.config.all_disc_password) {
                                self.gui.show_popup('error', {
                                    'title': _t('Error'),
                                    'body': _t('Incorrect password. Please try again'),
                                });
                            } else {
                                if (lines.length === 0) {
            this.gui.show_popup('error', {
                title : _t("No discount product found"),
                body  : _t("Please Select Same product First"),
            });
                 return;
        }
        if (lines.length > 0) {
        var i = 0;
        var rem = 0
        while ( i < lines.length ) {
           if(lines[i].discount>0){
           lines[i].set_discount(0);
           rem = 1

           }
            i++;
           }
        if(rem === 1 ){return;}

        }
        this.gui.show_popup('number',{
            'title': _t('Discount Percentage'),
            'value': 0.0,
            'confirm': function(val) {
                val = Math.round(Math.max(0,Math.min(100,val)));
                self.apply_discount(val);
            },
        });
                            }
                        },
                    });
                } else {

        if (lines.length === 0) {
            this.gui.show_popup('error', {
                title : _t("No discount product found"),
                body  : _t("Please Select Same product First"),
            });
                 return;
        }
        if (lines.length > 0) {
        var i = 0;
        var rem = 0
        while ( i < lines.length ) {
           if(lines[i].discount>0){
           lines[i].set_discount(0);
           rem = 1

           }
            i++;
           }
        if(rem === 1 ){return;}

        }
        this.gui.show_popup('number',{
            'title': _t('Discount Percentage'),
            'value': 0.0,
            'confirm': function(val) {
                val = Math.round(Math.max(0,Math.min(100,val)));
                self.apply_discount(val);
            },
        });
                        }

    },
    apply_discount: function(pc) {
        var order    = this.pos.get_order();
        var lines    = order.get_orderlines();
//        console.log('order== ',order);

        var i = 0;
        while ( i < lines.length ) {
            lines[i].set_discount(pc);
            console.log('lines[i].discount == ',lines[i].discount);
            i++;

        }
//
//        // Add discount
//        var discount = - pc / 100.0 * order.get_total_with_tax();
//
//        if( discount < 0 ){
//            order.add_product(product, { discount: pc });
//        }
    },
});

screens.define_action_button({
    'name': 'discount',
    'widget': DiscountButtonAll,

    },
);

return {
    DiscountButtonAll: DiscountButtonAll
}

});

