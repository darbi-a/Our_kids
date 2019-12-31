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
            var self = this;
            var current_date = new Date();
            var current_date_str = moment(current_date).format('YYYY-MM-DD')
            this.models.push({
                model:  'pos.promotion',
                fields: [],
                domain: function(self){ return [['date_from','<=',current_date_str],['date_to','>=',current_date_str],['pos_config_ids','in',self.config.id]] },
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
            if(this.pos_promotion_ids === undefined){
                this.pos_promotion_ids = [];
            }
//            this.pos_promotion_ids = [];

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

        add_product: function(product, options){
            var res = _super_order.add_product.apply(this,arguments);
            if(options && options.is_promotion){
                var selected_orderline = this.get_selected_orderline();
                selected_orderline.is_promotion = true;
                selected_orderline.promotion_id = options.promotion_id;
            }
            return res;
        },
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({


        export_as_JSON: function(){
            var json = _super_orderline.export_as_JSON.apply(this,arguments);
            if (this.is_promotion) {
                json.is_promotion = this.is_promotion;
                json.promotion_id = this.promotion_id;
            }
            if(this.applied_promotion_id) {
                json.applied_promotion_id = this.applied_promotion_id;
            }
            return json;
        },

        init_from_JSON: function(json){
            _super_orderline.init_from_JSON.apply(this,arguments);
            this.is_promotion = json.is_promotion;
            this.promotion_id = json.promotion_id;
            this.applied_promotion_id = json.applied_promotion_id;
        },
    });


//    var PromotionsButtonWidget = screens.ActionButtonWidget.extend({
//        template: 'PromotionsButtonWidget',
//        button_click: function() {
//            var self = this;
//            var selection_list = _.map(self.pos.db.promotions, function (promotion) {
//                return {
//                    label: promotion.name,
//                    item: promotion,
//                };
//            });
//            self.gui.show_popup('selection',{
//                title: _t('Apply Promotion'),
//                list: selection_list,
//                confirm: function (promotion) {
//                    var order = self.pos.get_order();
////                    for(var i = 0 ; i < order.pos_promotion_ids.length ; i++){
////                        if(promotion.id === order.pos_promotion_ids[i][1])
////                        {
////                            return;
////                        }
////                    }
//                    for(var i = 0 ; i < order.orderlines.models.length ; i++){
//                        var order_line = order.orderlines.models[i];
//                        if(order_line.product.id === promotion.ordered_product_id[0] ){
//                            var gift_product_id = promotion.gift_product_id[0];
//                            var gift_product = self.pos.db.get_product_by_id(gift_product_id);
//                            var order_gift_ratio = Math.floor(order_line.quantity / promotion.ordered_quantity)
//                            if(order_gift_ratio >= 1 && gift_product){
//                                var gift_qty = order_gift_ratio * promotion.gift_quantity;
//                                order_line.applied_promotion_id = promotion.id;
//                                order.add_product(gift_product, {
//                                    quantity: gift_qty,
//                                    price: 0.0,
//                                    discount: 100,
//                                    is_promotion: true,
//                                    promotion_id: promotion.id,
//                                    merge: false,
//                                });
//                                order.pos_promotion_ids.push([4,promotion.id]);
//                                break;
//                            }
//
//                        }
//                    }
//                    order.trigger('change');
//                },
//
//            });
//        },
//
//    });
//
//    screens.define_action_button({
//        'name': 'Promotions',
//        'widget': PromotionsButtonWidget,
//        'condition': function() {
//            return true;
//        },
//    });



screens.OrderWidget.include({

    update_summary: function(){
        var self = this;
        var order = this.pos.get_order();
        var applied_promotion_lines = {};
        var line_promotions = {};
        var lines_without_promotions = [];
        var discount_lines = [];

        _.each(order.orderlines.models,function(line){
            if(line.is_promotion){
                var promotion = line.promotion_id;
                line_promotions[promotion] = line;
            }
            else if(line.applied_promotion_id){
                var applied_promotion = line.applied_promotion_id;
                applied_promotion_lines[applied_promotion] = line;
            }
            else if(!line.discount){
                lines_without_promotions.push(line);
            }
            else if(line.discount && !line.price){
                discount_lines.push(line);
            }
        });

        var unused_promotions = _.filter(self.pos.db.promotions,function(promotion){
            for(var i = 0 ;i < order.pos_promotion_ids.length ;  i++){
                if (order.pos_promotion_ids[i][1] === promotion.id){
                    return false;
                }
            }
            return true;
        });
        _.each(self.pos.db.promotions,function(promotion){
            var promotion_id = promotion.id;
            var applied_line = applied_promotion_lines[promotion_id];
            var promotion_line = line_promotions[promotion_id];

            if(applied_line && promotion_line){
                var order_gift_ratio = Math.floor(applied_line.quantity / promotion.ordered_quantity);
                var gift_qty = order_gift_ratio * promotion.gift_quantity;
                if(gift_qty !== promotion_line.quantity){
                    if(gift_qty <= 0){
                        unused_promotions.push(promotion);
                        promotion_line.order.remove_orderline(promotion_line);
                        applied_line.applied_promotion_id = undefined;
                        order.pos_promotion_ids = _.filter(order.pos_promotion_ids, function(o){
                            return o[1] !== promotion_id;
                        });
                    }
                    else{
                        promotion_line.set_quantity(gift_qty);
                    }
                }
            }
            else if(applied_line && !discount_lines.length){
                unused_promotions.push(promotion);
                applied_line.applied_promotion_id = undefined;
                order.pos_promotion_ids = _.filter(order.pos_promotion_ids, function(o){
                    return o[1] !== promotion_id;
                });
            }
            else if(promotion_line){
                unused_promotions.push(promotion);
                promotion_line.order.remove_orderline(promotion_line);
                order.pos_promotion_ids = _.filter(order.pos_promotion_ids, function(o){
                    return o[1] !== promotion_id;
                });
            }
        });

        _.each(unused_promotions,function(promotion){
            _.each(lines_without_promotions,function(line){
                if(line.product.id === promotion.ordered_product_id[0] ){
                    var gift_product_id = promotion.gift_product_id[0];
                    var gift_product = self.pos.db.get_product_by_id(gift_product_id);
                    var order_gift_ratio = Math.floor(line.quantity / promotion.ordered_quantity)
                    if(order_gift_ratio >= 1 && gift_product){
                        var gift_qty = order_gift_ratio * promotion.gift_quantity;
                        line.applied_promotion_id = promotion.id;
                        order.pos_promotion_ids.push([4,promotion.id]);
                        order.add_product(gift_product, {
                            quantity: gift_qty,
                            price: 0.0,
                            discount: 100,
                            is_promotion: true,
                            promotion_id: promotion.id,
                            merge: false,
                        });

                    }

                }
            });

        });
        this._super();
    },

});







});