odoo.define('pos_lock_mode.lock_mode', function (require) {
    "use strict";

    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;
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


var _super_posmodel = models.PosModel.prototype;
models.PosModel = models.PosModel.extend({

    delete_current_order: function() {
        var self = this;
        if (self.config.lock_inactive_orders == true) {
            self.gui.show_popup('passwordinput', {
                'title': _t('Password ?'),
                confirm: function (pw) {
                    if (pw !== self.config.inactive_orders_pwd) {

                        self.gui.show_popup('error', {
                            'title': _t('Error'),
                            'body': _t('Incorrect password. Please try again'),
                        });
                    }
                    else{
                        _super_posmodel.delete_current_order.apply(self, arguments);
                    }
                },
            });

        }
        else {

            _super_posmodel.delete_current_order.apply(this, arguments);

        }
    },

});

gui.define_popup({name:'passwordinput', widget: PasswordInputPopupWidget});


    screens.set_fiscal_position_button.include({

        show_fiscal_screen: function(){

            var self = this;

//            var no_fiscal_position = [{
//                label: _t("None"),
//            }];
            var no_fiscal_position = [];
            var fiscal_positions = _.map(self.pos.fiscal_positions, function (fiscal_position) {
                return {
                    label: fiscal_position.name,
                    item: fiscal_position
                };
            });

            var selection_list = no_fiscal_position.concat(fiscal_positions);
            self.gui.show_popup('selection',{
                title: _t('Select tax'),
                list: selection_list,
                confirm: function (fiscal_position) {
                    var order = self.pos.get_order();
                    order.fiscal_position = fiscal_position;
                    // This will trigger the recomputation of taxes on order lines.
                    // It is necessary to manually do it for the sake of consistency
                    // with what happens when changing a customer.
                    _.each(order.orderlines.models, function (line) {
                        line.set_quantity(line.quantity);
                    });
                    order.trigger('change');
                },
                is_selected: function (fiscal_position) {
                    return fiscal_position === self.pos.get_order().fiscal_position;
                }
            });

        },

        button_click: function () {
            var self = this ;
            if (self.pos.config.lock_fiscal_position == true) {

                self.gui.show_popup('passwordinput', {
                    'title': _t('Password ?'),
                     confirm: function (pw) {
                        if (pw !== self.pos.config.fiscal_position_password) {
                            self.gui.show_popup('error', {
                                'title': _t('Error'),
                                'body': _t('Incorrect password. Please try again'),
                            });
                        } else {
                            return self.show_fiscal_screen();
                        }
                        },
                    });
                } else {
                    return self.show_fiscal_screen();
                }


        },

    });


    NumpadWidget.include({

        clickDeleteLastChar: function() {
            var self = this ;
            if (self.pos.config.lock_delete == true) {
                self.gui.show_popup('passwordinput', {
                    'title': _t('Password ?'),
                     confirm: function (pw) {
                        if (pw !== self.pos.config.delete_password) {
                            self.gui.show_popup('error', {
                                'title': _t('Error'),
                                'body': _t('Incorrect password. Please try again'),
                            });
                        } else {
                            return self.state.deleteLastChar();
                        }
                        },
                    });
            } else {
                return self.state.deleteLastChar();
            }

        },

        clickChangeMode: function (event) {
            var self = this;
            var mode = self.state.get('mode');
            var newMode = event.currentTarget.attributes['data-mode'].nodeValue;
            if (mode == newMode) {
                return self.state.changeMode(newMode);
            }
            if (newMode == 'discount') {
                if (self.pos.config.lock_discount == true) {
                    self.gui.show_popup('passwordinput', {
                        'title': _t('passwordinput ?'),
                        confirm: function (pw) {
                            if (pw !== self.pos.config.discount_password) {
                                self.gui.show_popup('error', {
                                    'title': _t('Error'),
                                    'body': _t('Incorrect password. Please try again'),
                                });
                            } else {
                                return self.state.changeMode(newMode);
                            }
                        },
                    });
                } else {
                    return self.state.changeMode(newMode);
                }
            } else if (newMode == 'price') {
                if (self.pos.config.lock_price == true) {
                    self.gui.show_popup('passwordinput', {
                        'title': _t('Password ?'),
                        confirm: function (pw) {
                            if (pw !== self.pos.config.price_password) {
                                self.gui.show_popup('error', {
                                    'title': _t('Error'),
                                    'body': _t('Incorrect password. Please try again'),
                                });
                            } else {
                                return self.state.changeMode(newMode);
                            }
                        },
                    });
                } else {
                    return self.state.changeMode(newMode);
                }
            } else {
                return self.state.changeMode(newMode);
            }
        },

        clickSwitchSign: function() {
            var self = this;

            if (self.pos.config.lock_change_sign == true) {
                self.gui.show_popup('passwordinput', {
                    'title': _t('Password ?'),
                    confirm: function (pw) {
                        if (pw !== self.pos.config.change_sign_pwd) {
                            self.gui.show_popup('error', {
                                'title': _t('Error'),
                                'body': _t('Incorrect password. Please try again'),
                            });
                        } else {
                            return self.state.switchSign();
                        }
                    },
                });
            } else {
                return self.state.switchSign();
            }

        },
    });


    Chrome.OrderSelectorWidget.include({

        order_click_handler: function(event,$el) {
            var order = this.get_order_by_uid($el.data('uid'));
            var self = this;
            if (self.pos.config.lock_inactive_orders == true) {
                self.gui.show_popup('passwordinput', {
                    'title': _t('Password ?'),
                    confirm: function (pw) {
                        if (pw !== self.pos.config.inactive_orders_pwd) {

                            self.gui.show_popup('error', {
                                'title': _t('Error'),
                                'body': _t('Incorrect password. Please try again'),
                            });
                        }
                        else{
                            if (order) {
                                this.pos.set_order(order);
                            }
                        }
                    },
                });

            }
            else {
                if (order) {
                    this.pos.set_order(order);
                }
            }
        },

    })

});