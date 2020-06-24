odoo.define('ourkids_access_rights.LinesWidget', function (require) {
'use strict';

var core = require('web.core');
var LinesWidget = require('stock_barcode.LinesWidget');

var QWeb = core.qweb;

LinesWidget.include({

    template: 'stock_barcode_lines_widget_modified',

    events: {
        'click .o_add_line': '_onClickAddLine',
        'click .o_validate_page': '_onClickValidatePage',
        'click .o_next_page': '_onClickNextPage',
        'click .o_previous_page': '_onClickPreviousPage',
        'click .o_put_in_pack': '_onPutInPack',
//        'click .o_save_page': '_onClickSavePage',
    },

    addProduct: function (lineDescription, model, doNotClearLineHighlight) {
        var $body = this.$el.filter('.o_barcode_lines');
        var $line = $(QWeb.render('stock_barcode_lines_template_modified', {
            lines: [lineDescription],
            groups: this.groups,
            model: model,
        }));
        $body.prepend($line);
        $line.on('click', '.o_edit', this._onClickEditLine.bind(this));
        $line.on('click', '.o_package_content', this._onClickTruckLine.bind(this));
        this._highlightLine($line, doNotClearLineHighlight);

        this._handleControlButtons();

        if (lineDescription.qty_done === 0) {
            this._toggleScanMessage('scan_lot');
        } else if (this.mode === 'receipt') {
            this._toggleScanMessage('scan_more_dest');
        } else if (['delivery', 'inventory'].indexOf(this.mode) >= 0) {
            this._toggleScanMessage('scan_more_src');
        } else if (this.mode === 'internal') {
            this._toggleScanMessage('scan_more_dest');
        } else if (this.mode === 'no_multi_locations') {
            this._toggleScanMessage('scan_products');
        }

    },

     _renderLines: function () {
         if (this.mode === 'done') {
             if (this.model === 'stock.picking') {
                 this._toggleScanMessage('picking_already_done');
             } else if (this.model === 'stock.inventory') {
                 this._toggleScanMessage('inv_already_done');
             }
             return;
         } else if (this.mode === 'cancel') {
             this._toggleScanMessage('picking_already_cancelled');
             return;
         }

        // Render and append the page summary.
        var $header = this.$el.filter('.o_barcode_lines_header');
        var $pageSummary = $(QWeb.render('stock_barcode_summary_template', {
            locationName: this.page.location_name,
            locationDestName: this.page.location_dest_name,
            nbPages: this.nbPages,
            pageIndex: this.pageIndex + 1,
            mode: this.mode,
            model: this.model,
        }));
        $header.append($pageSummary);

        // Render and append the lines, if any.
        var $body = this.$el.filter('.o_barcode_lines');
        if (this.page.lines.length) {
            var $lines = $(QWeb.render('stock_barcode_lines_template_modified', {
                lines: this.getProductLines(this.page.lines),
                packageLines: this.getPackageLines(this.page.lines),
                model: this.model,
                groups: this.groups,
            }));
            $body.prepend($lines);
            $lines.on('click', '.o_edit', this._onClickEditLine.bind(this));
            $lines.on('click', '.o_package_content', this._onClickTruckLine.bind(this));
        }
        // Toggle and/or enable the control buttons. At first, they're all displayed and enabled.
        var $next = this.$('.o_next_page');
        var $previous = this.$('.o_previous_page');
        var $validate = this.$('.o_validate_page');
        if (this.nbPages === 1) {
            $next.prop('disabled', true);
            $previous.prop('disabled', true);
        }
        if (this.pageIndex + 1 === this.nbPages) {
            $next.toggleClass('o_hidden');
            $next.prop('disabled', true);
        } else {
            $validate.toggleClass('o_hidden');
        }

        if (! this.page.lines.length) {
            $validate.prop('disabled', true);
        }

        this._handleControlButtons();

        if (this.mode === 'receipt') {
            this._toggleScanMessage('scan_products');
        } else if (['delivery', 'inventory'].indexOf(this.mode) >= 0) {
            this._toggleScanMessage('scan_src');
        } else if (this.mode === 'internal') {
            this._toggleScanMessage('scan_src');
        } else if (this.mode === 'no_multi_locations') {
            this._toggleScanMessage('scan_products');
        }

         var $summary_src = this.$('.o_barcode_summary_location_src');
         var $summary_dest = this.$('.o_barcode_summary_location_dest');

         if (this.mode === 'receipt') {
             $summary_dest.toggleClass('o_barcode_summary_location_highlight', true);
         } else if (this.mode === 'delivery' || this.mode === 'internal') {
             $summary_src.toggleClass('o_barcode_summary_location_highlight', true);
         }
     },

//     _onClickSavePage:function(ev){
//         ev.stopPropagation();
////         this.trigger_up('validate');
//
//     },




})


})