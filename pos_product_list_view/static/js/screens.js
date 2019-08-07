odoo.define('pos_product_list_view.screens', function (require) {
"use strict";

var module = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var gui = require('point_of_sale.gui');
var core = require('web.core');
var rpc = require('web.rpc');
var QWeb = core.qweb;
var _t = core._t;
var models = module.PosModel.prototype.models;
var PopupWidget = require('point_of_sale.popups');

var StockProductsQuantWidget = PopupWidget.extend({
    template:'StockProductsQuantWidget',
});


    gui.define_popup({name:'stock_products_quant', widget: StockProductsQuantWidget});

screens.ProductListWidget.include({

    render_product: function(product){
        var current_pricelist = this._get_active_pricelist();
        var cache_key = this.calculate_cache_key(product, current_pricelist);
        var cached = this.product_cache.get_node(cache_key);
        if(!cached){
            var product_html = QWeb.render('Product',{
                    widget:  this,
                    product: product,
                    pricelist: current_pricelist,
                    image_url: this.get_product_image_url(product),
                });
            var product_node = document.createElement('tbody');
            product_node.innerHTML = product_html;
            product_node = product_node.childNodes[1];
            this.product_cache.cache_node(cache_key,product_node);
            return product_node;
        }
        return cached;
    },

    show_stock_quant_popup: function(event) {
           var self = this;
           for(var i = 0; i < self.product_list.length; i++){
               if (self.product_list[i].id == event.target.id){
                    var product = self.product_list[i];
                    rpc.query({
                        model: 'stock.quant',
                        method: 'get_stock_quant',
                        args: [event.target.id],
                    }).then(function (res) {
                        var data = []
                        console.log(product);
                        for(var j = 0; j < res.length ; j++){
                            data.push({
                                location: res[j].location_id[1],
                                quantity: res[j].quantity,
                            })
                        }
                       self.gui.show_popup('stock_products_quant',{'data':data,'product_name':product.name})
                    });
               }
            }
    },


    renderElement: function() {
       var self = this;
        var el_str  = QWeb.render(this.template, {widget: this});
        var el_node = document.createElement('div');
            el_node.innerHTML = el_str;
            el_node = el_node.childNodes[1];

        if(this.el && this.el.parentNode){
            this.el.parentNode.replaceChild(el_node,this.el);
        }
        this.el = el_node;
        var list_container = el_node.querySelector('.product-list-contents');
        for(var i = 0, len = this.product_list.length; i < len; i++){
            var product_node = this.render_product(this.product_list[i]);
            product_node.addEventListener('click',this.click_product_handler);
//            product_node.addEventListener('keypress',this.keypress_product_handler);
            list_container.appendChild(product_node);
        }

        $('.product-stock').unbind().click( function(event) {
           event.stopPropagation();
           if(self.pos.config.lock_stock_qty){
                self.gui.show_popup('passwordinput',{
                    'title': _t('Fill Password'),
                    'confirm': function(val) {
                        var result = (self.pos.config.stock_amount_password == val);
                        if (result == true){

                            return self.show_stock_quant_popup(event);
                        }
                        else{
                            self.gui.show_popup('error', {
                                title : _t("Wrong Password"),
                                body  : _t("Your Password is Wrong"),
                            });

                        }

                    },
                    'cancel':  function(val){}
                })


           }else{

                self.show_stock_quant_popup(event);
           }



       });

    },
});
});