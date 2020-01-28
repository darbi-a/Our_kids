odoo.define('ourkids_access_rights.ClientAction', function (require) {
'use strict';

var ClientAction = require('stock_barcode.ClientAction');


ClientAction.include({

    _getState: function (recordId, state) {
        var self = this;
        var def;
        if (state) {
            def = $.Deferred().resolve(state);
        } else {
            def = this._rpc({
                'route': '/stock_barcode/get_set_barcode_view_state',
                'params': {
                    'record_id': recordId,
                    'mode': 'read',
                    'model_name': self.actionParams.model,
                },
            });
        }
        return def.then(function (res) {
            self.currentState = res[0];
            self.initialState = $.extend(true, {}, res[0]);
            self.title += self.initialState.name;
            self.groups = {
                'group_stock_multi_locations': self.currentState.group_stock_multi_locations,
                'group_tracking_owner': self.currentState.group_tracking_owner,
                'group_tracking_lot': self.currentState.group_tracking_lot,
                'group_production_lot': self.currentState.group_production_lot,
                'group_inventory_valuation': self.currentState.group_inventory_valuation,
                'group_uom': self.currentState.group_uom,
            };
            self.show_entire_packs = self.currentState.show_entire_packs;

            return res;
        });

    },


})


})