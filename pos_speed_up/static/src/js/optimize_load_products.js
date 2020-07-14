/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('pos_speed_up.optimize_load_products', function (require) {
    "use strict";
    var models = require('point_of_sale.models');
    var indexedDB = require('pos_speed_up.indexedDB');
    var rpc = require('web.rpc');
    var session = require('web.session');

    require('pos_speed_up.pos_model');

    if(!indexedDB){
        return;
    }

    models.PosModel = models.PosModel.extend({
        p_init: function () {
            var model = this.get_model('product.product');
            if (!model) {
                return;
            }
            if (indexedDB.is_cached(session.db + '_products')) {
                this.p_sync(model);
            } else {
                this.p_save(model);
            }
        },
        p_sync: function (model) {
            var pos = this;

            var client_version = localStorage.getItem(session.db + '_product_index_version');
            if (!/^\d+$/.test(client_version)) {
                client_version = 0;
            }

            rpc.query({
                model: 'product.index',
                method: 'synchronize',
                context: {location: pos.config && pos.config.stock_location_id && [pos.config.stock_location_id[0]] || [] },
                args: [client_version]
            }).then(function (res) {
                // update version
                localStorage.setItem(session.db + '_product_index_version', res['latest_version']);

                // create and delete
                var data_change = indexedDB.optimize_data_change(res['create'], res['delete'], res['disable']);

                model.domain.push(['id', 'in', data_change['create']]);

                pos.p_super_loaded = model.loaded;

                model.loaded = function (self, new_products) {
                    var done = new $.Deferred();

                    indexedDB.get(session.db + '_products').then(function (products) {

                        products = products.concat(new_products).filter(function (value) {
                            return data_change['delete'].indexOf(value.id) === -1;
                        });

                        // order_by product
                        indexedDB.order_by_in_place(products, ['sequence', 'default_code', 'name'], 'esc');

                        self.p_super_loaded(self, products);

                        done.resolve();

                    }).fail(function (error) {
                        console.log(error);
                        done.reject();
                    });

                    // put and delete product - indexedDB
                    indexedDB.get_object_store(session.db + '_products').then(function (store) {
                        _.each(new_products, function (product) {
                            store.put(product).onerror = function (ev) {
                                console.log(ev);
                                localStorage.setItem(session.db + '_product_index_version', client_version);
                            }
                        });
                        _.each(data_change['delete'], function (id) {
                            store.delete(id).onerror = function (ev) {
                                console.log(ev);
                                localStorage.setItem(session.db + '_product_index_version', client_version);
                            };
                        });
                    }).fail(function (error) {
                        console.log(error);
                        localStorage.setItem(session.db + '_product_index_version', client_version);
                    });

                    return done;
                };
            });
        },
        p_save: function (model) {
            this.p_super_loaded = model.loaded;
            model.loaded = function (self, products) {
                indexedDB.save(session.db + '_products', products);
                self.p_super_loaded(self, products);
            };
            this.p_update_version();
        },
        p_update_version: function () {
            var old_version = localStorage.getItem(session.db + '_product_index_version');
            var self = this;
            if (!/^\d+$/.test(old_version)) {
                old_version = 0;
            }
            rpc.query({
                model: 'product.index',
                method: 'get_latest_version',
                context: {location:self.config && self.config.stock_location_id && self.config.stock_location_id[0] || []},
                args: [old_version]
            }).then(function (res) {
                localStorage.setItem(session.db + '_product_index_version', res);
            });
        }
    });

    models.load_fields('product.product', ['sequence', 'name']);
});