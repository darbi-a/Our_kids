/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('pos_speed_up.pos_model', function (require) {
    "use strict";
    var models = require('point_of_sale.models');

    var _super_pos = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            this.p_init();

            var wait = this.get_model('res.users');
            if (wait) {
                var _super_loaded = wait.loaded;
                wait.loaded = function (self, users) {
                    var def = $.Deferred();
                    _super_loaded(self, users);

                    self.c_init().always(function () {
                        def.resolve();
                    });

                    return def;
                };
            }

            _super_pos.initialize.call(this, session, attributes);
        },
        get_model: function (_name) {
            var _index = this.models.map(function (e) {
                return e.model;
            }).indexOf(_name);
            if (_index > -1) {
                return this.models[_index]
            }
            return false;
        },
        c_init: function () {

        },
        c_save: function (model) {

        },
        c_sync: function (model) {

        },
        p_init: function () {

        },
        p_save: function (model) {

        },
        p_sync: function (model) {

        }
    });
});