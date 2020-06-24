odoo.define('ourkids_access_rights.HeaderWidget', function (require) {
'use strict';

var Widget = require('web.Widget');
var HeaderWidget = require('stock_barcode.HeaderWidget');

HeaderWidget.include({


    init: function (parent) {
        this._super.apply(this, arguments);
        this.title = parent.title;
    },


    /**
     * Handles the click on the `settings button`.
     *
     * @private
     * @param {MouseEvent} ev
     */
     _onClickShowSettings: function (ev) {
//        ev.stopPropagation();
        if(this.__parentedParent.groups.group_stock_manager){
            this._super.apply(this, arguments);
        }

    },


});

});
