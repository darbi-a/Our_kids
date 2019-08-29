odoo.define("pos_product_list_view.models", function (require) {
    "use strict";
    
    var pos_model = require('point_of_sale.models');
    
    pos_model.load_fields("product.product",['qty_available','default_code','list_price','season_id']);

//    var _super_posmodel = pos_model.PosModel.prototype;
//    pos_model.PosModel = pos_model.PosModel.extend({
//
//        initialize: function (session, attributes) {
//            var product_model = _.find(this.models, function(model){ return model.model === 'product.product'; });
//            product_model.context = function(self){ return { location: self.config.stock_location_id[0] }; };
////            product_model.context = function(self){ return { location: self.config.stock_location_id[0] , display_default_code: false }; };
//            return _super_posmodel.initialize.call(this, session, attributes);
//        },
//    })
    
    
});