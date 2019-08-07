odoo.define('pos_lock_session.session_lock', function (require) {
"use strict";

var core = require('web.core');
var chrome = require('point_of_sale.chrome');
var gui = require('point_of_sale.gui');
var PopupWidget = require('point_of_sale.popups');
var _t = core._t;

var SessionLock = PopupWidget.extend({
    template:'SessionLock',
    events: _.extend({}, PopupWidget.prototype.events,{
        "click .screen_lock" : "unlock_screen",
    }),
    show: function(options){
        var self = this;
        this._super(options);
        $(document).keydown(function(e) {
            if(e.keyCode == 13) {
                e.preventDefault();
                self.gui.show_screen('login',{lock:true});
            }
        });
    },
    unlock_screen:function(){
        var self = this;
        this.gui.show_screen('login',{lock:true});
    }
});
gui.define_popup({name:'lock', widget: SessionLock});


chrome.Chrome.include({
    events: {
            "click .pos-lock": "on_click_pos_lock",
        },

//    init: function() {
//        var self = this;
//        this._super();
////        $(document).keydown(function(e) {
////            if(self.pos.config.pos_lock){
////                if(e.keyCode == 76 && e.ctrlKey) {
////                    e.preventDefault();
////                    e.stopPropagation();
////                    self.gui.show_popup('lock',{});
////                }
////            }
////        });
//    },

    logout_idle:function(){
        if( this.pos.config.pos_lock){

            var configured_time = this.pos.config.time_before_close;
            var multiplier = 1;
            var time_unit = this.pos.config.time_unit;
            if(time_unit == 'sec'){
                multiplier = 1000;
            }
            else if(time_unit == 'min'){
                multiplier = 60*1000;
            }
            else if(time_unit == 'hours'){
                multiplier = 60*60*1000;
            }
            var time_out = multiplier*configured_time;
            var self = this;
            var t;
            //window.onload = resetTimer;
            //        window.onmousemove = resetTimer; // catches mouse movements
            //        window.onmousedown = resetTimer; // catches mouse movements
            window.onclick = resetTimer;     // catches mouse clicks
            window.onscroll = resetTimer;    // catches scrolling
            window.onkeypress = resetTimer;  //catches keyboard actions

            function logout() {
                self.gui.show_screen('login',{lock:true});
            }

            function resetTimer() {
                clearTimeout(t);
                t = setTimeout(logout, time_out);  // time is in milliseconds (1000 is 1 second)
            }
        }
    },

    renderElement: function(){
        var self = this;
        return this._super();

    },

    build_widgets: function(){
        this._super();
        var lock_pswd = this.pos.config.lock_screen_pwd ;
        this.logout_idle();
        if (this.pos.config.pos_lock && lock_pswd) {
            this.gui.set_startup_screen('login');
        }
    },

    on_click_pos_lock: function (e) {
        var self = this;
        e.stopPropagation();
        self.gui.show_popup('lock',{});
    },

});

});