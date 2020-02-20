odoo.define('pos_loyalty_extend.loyalty_extend', function(require) {
"use strict";

var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var core = require('web.core');
var utils = require('web.utils');

var round_pr = utils.round_precision;
var QWeb     = core.qweb;

var _t = core._t;

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({

        initialize: function (session, attributes) {
            var product_model = _.find(this.models, function(model){ return model.model === 'loyalty.program'; });
            product_model.fields.push('pp_payment_visa','pp_payment_cash');

            return _super_posmodel.initialize.call(this, session, attributes);
        },
    });

var _super = models.Order;
models.Order = models.Order.extend({

    /* The total of points won, excluding the points spent on rewards */
    get_won_points: function(){
        if (!this.pos.loyalty || !this.get_client()) {
            return 0;
        }

        var orderLines = this.get_orderlines();
        var rounding   = this.pos.loyalty.rounding;

        var product_sold = 0;
        var total_sold   = 0;
        var total_points = 0;

        for (var i = 0; i < orderLines.length; i++) {
            var line = orderLines[i];
            var product = line.get_product();
            var rules  = this.pos.loyalty.rules_by_product_id[product.id] || [];
            var overriden = false;

            if (line.get_reward()) {  // Reward products are ignored
                continue;
            }

            for (var j = 0; j < rules.length; j++) {
                var rule = rules[j];
                total_points += round_pr(line.get_quantity() * rule.pp_product, rounding);
                total_points += round_pr(line.get_price_with_tax() * rule.pp_currency, rounding);
                // if affected by a non cumulative rule, skip the others. (non cumulative rules are put
                // at the beginning of the list when they are loaded )
                if (!rule.cumulative) {
                    overriden = true;
                    break;
                }
            }

            // Test the category rules
            if ( product.pos_categ_id ) {
                var category = this.pos.db.get_category_by_id(product.pos_categ_id[0]);
                while (category && !overriden) {
                    var rules = this.pos.loyalty.rules_by_category_id[category.id] || [];
                    for (var j = 0; j < rules.length; j++) {
                        var rule = rules[j];
                        total_points += round_pr(line.get_quantity() * rule.pp_product, rounding);
                        total_points += round_pr(line.get_price_with_tax() * rule.pp_currency, rounding);
                        if (!rule.cumulative) {
                            overriden = true;
                            break;
                        }
                    }
                    var _category = category;
                    category = this.pos.db.get_category_by_id(this.pos.db.get_category_parent_id(category.id));
                    if (_category === category) {
                        break;
                    }
                }
            }

            if (!overriden) {
                product_sold += line.get_quantity();
                total_sold   += line.get_price_with_tax();
            }
        }
//        var payment_method_factor = 1;
        if(this.finalized){
            var payments = this.paymentlines.models;
            var total_visa_payments = 0;
            for(var i = 0; i < payments.length ; i++){
                if(payments[i].cashregister.journal.type === 'bank'){
                    total_visa_payments = total_visa_payments + payments[i].cashregister.amount;
                }
            }
            var visa_factor = this.pos.loyalty.pp_payment_visa;
            var cash_factor = this.pos.loyalty.pp_payment_cash;
            var total_payment_points = this.pos.loyalty.pp_currency * (total_visa_payments * visa_factor + (total_sold - total_visa_payments) * cash_factor);
            total_points += round_pr( total_payment_points, rounding );
        }

//        total_points += round_pr( total_sold*payment_method_factor * this.pos.loyalty.pp_currency, rounding );
        total_points += round_pr( product_sold * this.pos.loyalty.pp_product, rounding );
        total_points += round_pr( this.pos.loyalty.pp_order, rounding );

        return total_points;
    },
})

});