odoo.define('mt_pos.pos_discount', function (require) {
"use strict";

var core = require('web.core');
var screens = require('point_of_sale.screens');
var _t = core._t;

    var PopupWidget = require('point_of_sale.popups');
    var gui     = require('point_of_sale.gui');

function enable_buttons(){
    $('.coupon_button').removeClass('button_disabled');
    $('.coupon_button').removeClass('button_coupon');
    $('.js_discount').removeClass('button_coupon');
    $('.control-button:nth-child(1)').removeClass('button_coupon');
    $('.leftpane .numpad').removeClass('numpad-button-disable');
    $('div.rightpane').removeClass('rightpane-disable');
    $('button.set-customer').removeClass('set-customer-disable');

}

var DiscountTypePopupWidget = PopupWidget.extend({
    template: 'DiscountTypePopupWidget',
    show: function(options){
        options = options || {};
        this._super(options);

        this.renderElement();
//        this.$('input,textarea').focus();
    },
    click_confirm: function(){
          var value = this.$('#discount_type').val();
          console.log('value');
          console.log(value);
        this.gui.close_popup();
        if( this.options.confirm ){
            this.options.confirm.call(this,value);
        }
    },
});
gui.define_popup({name:'discounttype', widget: DiscountTypePopupWidget});



var DiscountButton = screens.ActionButtonWidget.extend({
    template: 'DiscountButton1',
    button_click: function(){
        var self = this;

            if(this.pos.config.lock_global_discount){
                this.gui.show_popup('passwordinput',{
                    'title': _t('Fill Password'),
                    'confirm': function(val) {
                        var result = self.validate_pwd(val);
                        if (result == true){

                            self.show_discount();
                        }
                        else{
                            this.gui.show_popup('error', {
                                title : _t("Wrong Password"),
                                body  : _t("Your Password is Wrong"),
                            });

                        }

                    },
                    'cancel':  function(val){}
                })


            }else{

                this.show_discount();
//           var val = this.pos.config.discount_pc;
//           this.gui.show_popup('number',{
//               'title': _t('Discount Percentage'),
//               'value': this.pos.config.discount_pc,
//               'confirm': function(val) {
//                    val = Math.round(Math.max(0,Math.min(100,val)));
//                    self.apply_discount(val);
//
//                }
//            });
            }
},


    validate_pwd: function(val){
        if (val == this.pos.config.global_discount_password){
            return true;
        }else{
            return false;
        }
    },
    apply_discount: function(pc) {
        var order    = this.pos.get_order();
        var lines    = order.get_orderlines();
        var product  = this.pos.db.get_product_by_id(this.pos.config.discount_product_id[0]);
        if (product === undefined) {
            this.gui.show_popup('error', {
                title : _t("No discount product found"),
                body  : _t("The discount product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."),
            });
            return;
        }

        // Remove existing discounts
        var i = 0;
        while ( i < lines.length ) {
            if (lines[i].get_product() === product) {
                order.remove_orderline(lines[i]);
            } else {
                i++;
            }
        }

        // Add discount
        var discount = - pc / 100.0 * (order.get_total_with_tax());

        if( discount < 0 ){
            order.add_product(product, { price: discount });
        }
    },

    apply_fixed_discount: function(val) {
        var order    = this.pos.get_order();
        var lines    = order.get_orderlines();
        var product  = this.pos.db.get_product_by_id(this.pos.config.discount_product_id[0]);
        if (product === undefined) {
            this.gui.show_popup('error', {
                title : _t("No discount product found"),
                body  : _t("The discount product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."),
            });
            return;
        }
       if (order.get_total_with_tax() < val) {
            this.gui.show_popup('error', {
                title : _t("Fixed Discount Larger Than order"),
                body  : _t("Fixed Discount Larger Than order."),
            });
            return;
        }

        // Remove existing discounts
        var i = 0;
        while ( i < lines.length ) {
            if (lines[i].get_product() === product) {
                order.remove_orderline(lines[i]);
            } else {
                i++;
            }
        }

        // Add discount
        var discount = - val;

        if( discount < 0 ){
            order.add_product(product, { price: discount });
        }
    },

    show_discount:function(){
        var self = this;
        var order    = this.pos.get_order();
        if(order.discount_mode){

            for (var i = 0 ; i < order.orderlines.models.length; i++){
                var line = order.orderlines.models[i];
                if(line.price < 0 && line.product.is_discount){
                    order.remove_orderline(order.orderlines.models[i]);
                }
            }
            order.discount_mode = !order.discount_mode;
            enable_buttons();
        }
         this.gui.show_popup('discounttype',{
        'confirm': function(val) {
            if(val === 'percentage'){
                var value = this.pos.config.discount_pc
                this.gui.show_popup('number',{
                    'title': _t('Discount Percentage'),
                    'value': this.pos.config.discount_pc,
                    'confirm': function(value) {
                        val = Math.round(Math.max(0,Math.min(100,value)));
                        self.apply_discount(val);
                    },
                })
            }
            if(val === 'fixed'){
                this.gui.show_popup('number',{
                    'title': _t('Discount Value'),
                    'value': 0.0,
                    'confirm': function(value) {
                        self.apply_fixed_discount(value);
                    },
                })
            }

        }

     });

    }
});

screens.define_action_button({
    'name': 'discount',
    'widget': DiscountButton,
    'condition': function(){
        return this.pos.config.module_pos_discount && this.pos.config.discount_product_id;
    },
});

});
