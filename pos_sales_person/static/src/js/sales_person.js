odoo.define('pos_sales_person.sales_person', function(require) {
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
            this.models.push({
                model:  'hr.employee',
                fields: ['id','name','pos_code'],
                domain: function(self){ return [['id','in',self.config.sale_persons_ids]]; },
                loaded: function(self, sale_persons){
                    self.db.sale_persons = sale_persons;
                    console.log(sale_persons);
                }
            })

            return _super_posmodel.initialize.call(this, session, attributes);
        },
    });

var _super_order = models.Order.prototype;
models.Order = models.Order.extend({

//        initialize: function(attributes,options){
//            _super_order.initialize.apply(this, arguments);
//            this.pos_promotion_ids = [];
//
//        },

        export_as_JSON: function(){
            var json = _super_order.export_as_JSON.apply(this,arguments);
            if (this.sale_person_code) {
                json.sale_person_code = this.sale_person_code;
            }
            if (this.sale_person_id) {
                json.sale_person_id = this.sale_person_id;
            }
            return json;
        },

        init_from_JSON: function(json){
            _super_order.init_from_JSON.apply(this,arguments);
            this.sale_person_id = json.sale_person_id;
            this.sale_person_code = json.sale_person_code;
        },
})

var SalePersonButtonWidget = screens.ActionButtonWidget.extend({
    template: 'SalePersonButtonWidget',
    button_click: function() {
        var self = this;
        var selection_list = _.map(self.pos.db.sale_persons, function (sale_person) {
            return {
                label: sale_person.name,
                item: sale_person,
            };
        });
        self.gui.show_popup('selection',{
            title: _t('Sale Person'),
            list: selection_list,
            confirm: function (sale_person) {
                var order = self.pos.get_order();
                order.sale_person_id = sale_person.id;
                order.sale_person_code = sale_person.pos_code;
                order.trigger('change');
//                $('.sale_person_button').text(sale_person.pos_code);
            },

        });
    },

});

screens.define_action_button({
    'name': 'SalePerson',
    'widget': SalePersonButtonWidget,
    'condition': function() {
        return true;
    },
});



});