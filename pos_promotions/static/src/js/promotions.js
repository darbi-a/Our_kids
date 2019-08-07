odoo.define('pos_promotions.promotions', function (require) {
    "use strict";

    var chrome = require('point_of_sale.chrome');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var _t = core._t;

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({

        initialize: function (session, attributes) {
            var current_date = new Date();
            var current_date_str = moment(current_date).format('YYYY-MM-DD')
            this.models.push({
                model:  'pos.promotion',
                fields: [],
                domain: [['date_from','<=',current_date_str],['date_to','>=',current_date_str]],
                loaded: function(self, promotions){
                    self.db.promotions = promotions;
//                    console.log(promotions);
                }
            }
            )

            return _super_posmodel.initialize.call(this, session, attributes);
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attributes,options){
            _super_order.initialize.apply(this, arguments);
            this.pos_promotion_ids = [];

        },

            export_as_JSON: function(){
            var json = _super_order.export_as_JSON.apply(this,arguments);
            if (this.pos_promotion_ids) {
                json.pos_promotion_ids = this.pos_promotion_ids;
            }
            return json;
        },

        init_from_JSON: function(json){
            _super_order.init_from_JSON.apply(this,arguments);
            this.pos_promotion_ids = json.pos_promotion_ids;
        },
    });


    var PromotionsButtonWidget = screens.ActionButtonWidget.extend({
        template: 'PromotionsButtonWidget',
        button_click: function() {
            var self = this;
            var selection_list = _.map(self.pos.db.promotions, function (promotion) {
                return {
                    label: promotion.name,
                    item: promotion,
                };
            });
            self.gui.show_popup('selection',{
                title: _t('Apply Promotion'),
                list: selection_list,
                confirm: function (promotion) {
                    var order = self.pos.get_order();
                    for(var i = 0 ; i < order.pos_promotion_ids.length ; i++){
                        if(promotion.id === order.pos_promotion_ids[i][1])
                        {
                            return;
                        }
                    }
                    for(var i = 0 ; i < order.orderlines.models.length ; i++){
                        var order_line = order.orderlines.models[i];
                        if(order_line.product.id === promotion.ordered_product_id[0] ){
                            var gift_product_id = promotion.gift_product_id[0];
                            var gift_product = self.pos.db.get_product_by_id(gift_product_id);
                            var order_gift_ratio = Math.floor(order_line.quantity / promotion.ordered_quantity)
                            if(order_gift_ratio >= 1 && gift_product){
                                var gift_qty = order_gift_ratio * promotion.gift_quantity;
                                order.add_product(gift_product, {
                                    quantity: gift_qty,
                                    price: 0.0,
                                    discount: 100,
                                });
                                order.pos_promotion_ids.push([4,promotion.id]);
                                break;
                            }

                        }
                    }
                    order.trigger('change');
                },

            });
        },

    });

    screens.define_action_button({
        'name': 'Promotions',
        'widget': PromotionsButtonWidget,
        'condition': function() {
            return true;
        },
    });



//screens.OrderWidget.include({
//
//    update_summary: function(){
//        this._super();
//        var order = this.pos.get_order();
//        var available_promotions = _.each(order.pos_promotion_ids,function(promotion){
//
//        });
//    },
//
//});







});