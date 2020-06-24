odoo.define('ourkids_access_rights.MainMenu', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var Dialog = require('web.Dialog');
var Session = require('web.session');
var MainMenu = require('stock_barcode.MainMenu').MainMenu;

var _t = core._t;

MainMenu.include({

    events: _.defaults({
        "click .button_operations": function(){
            if(this.group_stock_manager){
                this.do_action('stock_barcode.stock_picking_type_action_kanban');
            }else{
                this.do_action('ourkids_access_rights.stock_picking_type_action_kanban');
            }

        },
    }, MainMenu.prototype.events),

    willStart: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            return Session.user_has_group('stock.group_stock_manager').then(function (has_group) {
                self.group_stock_manager = has_group;
            });
        });
    },
})

})
