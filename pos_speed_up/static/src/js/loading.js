/*
* @Author: D.Jane
* @Email: jane.odoo.sp@gmail.com
*/
odoo.define('pos_speed_up.loading', function (require) {
    "use strict";

    var chrome = require('point_of_sale.chrome');
    var indexedDB = require('pos_speed_up.indexedDB');

    chrome.Chrome.include({
        loading_progress: function(fac){
            this._super(fac);
            this.$('.loader .loader-feedback .my-percent').text(Math.floor(fac*100)+'%');
        },
        renderElement: function () {
            this._super();
            if (indexedDB.is_cached('products')) {
                this.$('.loader .loader-feedback .my-message').hide();
            } else {
                this.$('.loader .loader-feedback .message').hide();
            }
        }
    });
});