/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('pos_speed_up.optimize_load_customers', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var indexedDB = require('pos_speed_up.indexedDB');
    var rpc = require('web.rpc');

    require('pos_speed_up.pos_model');

    if (!indexedDB) {
        return;
    }
    
    // for default sorted
    models.load_fields('res.partner', ['display_name']);

    models.PosModel = models.PosModel.extend({
        c_init: function () {
            var def = new $.Deferred();
            var model = this.get_model('res.partner');
            if (!model) {
                def.reject();
            }
            if (indexedDB.is_cached('customers')) {
                this.c_sync(model).then(function () {
                    def.resolve();
                }).fail(function () {
                    def.reject();
                });
            } else {
                this.c_save(model);
                def.resolve();
            }
            return def.promise();
        },
        c_sync: function (model) {
            var def = $.Deferred();
            var pos = this;

            var client_version = localStorage.getItem('customer_index_version');
            if (!/^\d+$/.test(client_version)) {
                client_version = 0;
            }

            rpc.query({
                model: 'customer.index',
                method: 'synchronize',
                args: [client_version]
            }).then(function (res) {
                // update version
                localStorage.setItem('customer_index_version', res['latest_version']);

                // create and delete
                var data_change = indexedDB.optimize_data_change(res['create'], res['delete'], res['disable']);

                model.domain.push(['id', 'in', data_change['create']]);

                pos.c_super_loaded = model.loaded;

                model.loaded = function (self, new_customers) {
                    var done = new $.Deferred();

                    indexedDB.get('customers').then(function (customers) {
                        customers = customers.concat(new_customers).filter(function (value) {
                            return data_change['delete'].indexOf(value.id) === -1;
                        });
                        // order_by
                        indexedDB.order_by_in_place(customers, ['display_name'], 'esc');
                        self.c_super_loaded(self, customers);

                        done.resolve();
                    }).fail(function (error) {
                        console.log(error);
                        localStorage.setItem('customer_index_version', client_version);
                        done.reject();
                    });


                    // put and delete customer - indexedDB
                    indexedDB.get_object_store('customers').then(function (store) {
                        _.each(new_customers, function (customer) {
                            store.put(customer).onerror = function (ev) {
                                console.log(ev);
                                localStorage.setItem('customer_index_version', client_version);
                            }
                        });
                        _.each(data_change['delete'], function (id) {
                            store.delete(id).onerror = function (ev) {
                                console.log(ev);
                                localStorage.setItem('customer_index_version', client_version);
                            };
                        });
                    }).fail(function (error) {
                        console.log(error);
                        localStorage.setItem('customer_index_version', client_version);
                    });

                    return done;
                };

                def.resolve();
            }).fail(function (error) {
                console.log(error);
                def.reject();
            });

            return def.promise();
        },
        c_save: function (model) {
            this.c_super_loaded = model.loaded;
            model.loaded = function (self, customers) {
                indexedDB.save('customers', customers);
                self.c_super_loaded(self, customers);
            };
            this.c_update_version();
        },
        c_update_version: function () {
            var old_version = localStorage.getItem('customer_index_version');
            if (!/^\d+$/.test(old_version)) {
                old_version = 0;
            }
            rpc.query({
                model: 'customer.index',
                method: 'get_latest_version',
                args: [old_version]
            }).then(function (res) {
                localStorage.setItem('customer_index_version', res);
            });
        }
    });
});