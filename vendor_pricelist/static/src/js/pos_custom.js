odoo.define('vendor_pricelist.vendor_pricelist', function (require) {
"use strict";

var screens = require('point_of_sale.screens');
var models = require('point_of_sale.models');
var core = require('web.core');

var QWeb = core.qweb;

var _super_orderline = models.Orderline.prototype;

var PosBaseWidget = require('point_of_sale.BaseWidget');
var gui = require('point_of_sale.gui');
var models = require('point_of_sale.models');
var core = require('web.core');
var rpc = require('web.rpc');
var utils = require('web.utils');
var field_utils = require('web.field_utils');
var BarcodeEvents = require('barcodes.BarcodeEvents').BarcodeEvents;

var QWeb = core.qweb;
var _t = core._t;

var round_pr = utils.round_precision;

var _super_posmodel = models.PosModel.prototype;

models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
        // Add field to model
        var partner_model = _.find(this.models, function(model){
            return model.model === 'res.partner';
        });
        partner_model.fields.push('ref');
        var product_model = _.find(this.models, function(model){
            return model.model === 'product.product';
        });
        product_model.fields.push('vendor_num');

        // run Super
        return _super_posmodel.initialize.call(this, session, attributes)
        },

});
models.Product = models.Product.extend({
 get_price: function(pricelist, quantity){
        var self = this;
        var date = moment().startOf('day');

        // In case of nested pricelists, it is necessary that all pricelists are made available in
        // the POS. Display a basic alert to the user in this case.
        if (pricelist === undefined) {
            alert(_t(
                'An error occurred when loading product prices. ' +
                'Make sure all pricelists are available in the POS.'
            ));
        }

        var category_ids = [];
        var category = this.categ;
        while (category) {
            category_ids.push(category.id);
            category = category.parent;
        }

        var pricelist_items = _.filter(pricelist.items, function (item) {
            console.log('item == > ',item)
            console.log('item.product_id  == > ',item.product_id )
            console.log('item.vendor_num  == > ',item.vendor_num)
            console.log('self.vendor_num  == > ',self.vendor_num)
            return (! item.product_tmpl_id || item.product_tmpl_id[0] === self.product_tmpl_id) &&
                   (! item.product_id || item.product_id[0] === self.id) &&
                   (! item.vendor_num || item.vendor_num === self.vendor_num) &&
                   (! item.categ_id || _.contains(category_ids, item.categ_id[0])) &&
                   (! item.date_start || moment(item.date_start).isSameOrBefore(date)) &&
                   (! item.date_end || moment(item.date_end).isSameOrAfter(date));
        });

        var price = self.lst_price;
        _.find(pricelist_items, function (rule) {
            if (rule.min_quantity && quantity < rule.min_quantity) {
                return false;
            }

            if (rule.base === 'pricelist') {
                price = self.get_price(rule.base_pricelist, quantity);
            } else if (rule.base === 'standard_price') {
                price = self.standard_price;
            }

            if (rule.compute_price === 'fixed') {
                price = rule.fixed_price;
                return true;
            } else if (rule.compute_price === 'percentage') {
                price = price - (price * (rule.percent_price / 100));
                return true;
            } else {
                var price_limit = price;
                price = price - (price * (rule.price_discount / 100));
                if (rule.price_round) {
                    price = round_pr(price, rule.price_round);
                }
                if (rule.price_surcharge) {
                    price += rule.price_surcharge;
                }
                if (rule.price_min_margin) {
                    price = Math.max(price, price_limit + rule.price_min_margin);
                }
                if (rule.price_max_margin) {
                    price = Math.min(price, price_limit + rule.price_max_margin);
                }
                return true;
            }

            return false;
        });

        // This return value has to be rounded with round_di before
        // being used further. Note that this cannot happen here,
        // because it would cause inconsistencies with the backend for
        // pricelist that have base == 'pricelist'.
        return price;

    },
 });


});