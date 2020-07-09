# -*- coding: utf-8 -*-
""" Products Stock Slow Move """

import xlwt
import base64
from io import BytesIO
from datetime import datetime
from odoo import fields, models, api, _, tools, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

import logging

LOGGER = logging.getLogger(__name__)


class ProductsSlowMove(models.TransientModel):
    _name = 'stock.product.slow.move'
    _description = 'Products Slow Move'

    start_date = fields.Date(
        required=True
    )
    end_date = fields.Date(
        required=True
    )
    partner_ids = fields.Many2many(
        comodel_name="res.partner",
        string="Vendor",
        domain=[('supplier', '=', True)]
    )

    season_ids = fields.Many2many(
        comodel_name="product.season",
    )

    stock_location_ids = fields.Many2many(
        comodel_name="stock.location",
        string="Branch",
        domain=[('usage', '=', 'customer')]
    )

    category_ids = fields.Many2many(
        comodel_name='product.category',
    )

    def get_report_data(self):
        data = []
        stock_move = self.env['stock.move']
        partners = self.partner_ids and self.partner_ids
        start_date = str(fields.Datetime.from_string(self.start_date))
        end_date = str(fields.Datetime.from_string(self.end_date))
        seasons = self.season_ids
        categories = self.category_ids and \
                     self.env['product.category'].search([('id', 'child_of', self.category_ids.ids)])
        domain = [('date', '>=', start_date), ('date', '<=', end_date), ('state', '=', 'done')]
        locations = self.stock_location_ids or self.env['stock.location'].search([('usage', '=', 'customer')])
        domain += locations and [('location_dest_id', 'in', locations.ids)]
        moves = stock_move.search(domain)
        products = moves.mapped('product_id')
        partners_refs = partners and filter(None, partners.mapped('ref'))
        query = """
            select p.id  As product_id from 
            product_product p join product_template t on (p.product_tmpl_id=t.id)
            WHERE
            p.id not in %s """
        query += seasons and " and p.season_id in %s" or ""
        query += categories and " and t.categ_id in %s" or ""
        query += partners_refs and " and p.vendor_num in %s" or ""
        args = [tuple(products.ids)]
        args += seasons and [tuple(seasons.ids)]
        args += categories and [tuple(categories.ids)]
        args += partners_refs and [tuple(partners_refs)]
        self.env.cr.execute(query, args)
        product_ids = [x[0] for x in self.env.cr.fetchall()]
        products = self.env['product.product'].browse(product_ids)
        print(len(products))
        for product in products:
            qty_available = product.qty_available
            last_po = stock_move.search([('product_id', '=', product.id),
                                         ('location_id.usage', '=', 'supplier')], order='create_date desc', limit=1)
            last_so = stock_move.search([('product_id', '=', product.id),
                                         ('location_dest_id.usage', '=', 'customer')], order='create_date desc',
                                        limit=1)
            data.append({
                 'product_barcode': product.barcode,
                 'product_code': product.default_code,
                 'product_name': product.name,
                 'aval_qty': qty_available ,
                 'list_price': product.list_price,
                 'standard_price': product.standard_price,
                 'cost_price': qty_available * product.standard_price,
                 'sale_price': qty_available * product.sale_price,
                 'last_po_date':  last_po and str(last_po.date.date()) or '',
                 'last_so_date':  last_so and str(last_so.date.date()) or '',
            })
        return data

    def action_print_report(self):
        self.ensure_one()
        data = self.get_report_data()
        workbook = xlwt.Workbook()
        TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, color-index black,height 300;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour tan, pattern_back_colour tan'
        )

        TABLE_SUB_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, color-index black,height 180;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour tan, pattern_back_colour tan'
        )

        TABLE_HEADER_batch = xlwt.easyxf(
            'font: bold 1, name Tahoma, color-index black,height 160;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour light_green, pattern_back_colour light_green'
        )
        header_format = xlwt.easyxf(
            'font: bold 1, name Aharoni , color-index black,height 200;'
            'align: vertical center, horizontal center, wrap off;'
            'alignment: wrap 1;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour gray25, pattern_back_colour gray25'
        )

        TABLE_HEADER_Data = TABLE_HEADER
        TABLE_HEADER_Data.num_format_str = '#,##0.00_);(#,##0.00)'
        STYLE_LINE = xlwt.easyxf(
            'align: vertical center, horizontal center, wrap off;',
            'borders: left thin, right thin, top thin, bottom thin; '
            # 'num_format_str: General'
        )

        TABLE_data = xlwt.easyxf(
            'font: bold 1, name Aharoni, color-index black,height 150;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour white, pattern_back_colour white'
        )
        TABLE_data.num_format_str = '#,##0.00'
        xlwt.add_palette_colour("gray11", 0x11)
        workbook.set_colour_RGB(0x11, 222, 222, 222)
        TABLE_data_tolal_line = xlwt.easyxf(
            'font: bold 1, name Aharoni, color-index white,height 200;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour blue_gray, pattern_back_colour blue_gray'
        )

        TABLE_data_tolal_line.num_format_str = '#,##0.00'
        TABLE_data_o = xlwt.easyxf(
            'font: bold 1, name Aharoni, color-index black,height 150;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour gray11, pattern_back_colour gray11'
        )
        STYLE_LINE_Data = STYLE_LINE
        STYLE_LINE_Data.num_format_str = '#,##0.00_);(#,##0.00)'

        worksheet = workbook.add_sheet(_('تقرير الرواكد'))
        worksheet.cols_right_to_left = 1
        row = 0
        col = 0
        worksheet.write_merge(row, row + 1, col + 2, col + 6, _('تقرير الرواكد'), TABLE_HEADER)
        row += 3
        worksheet.write(row, col, _('التاريخ'), TABLE_SUB_HEADER)
        col += 1
        worksheet.write(row, col, datetime.strftime(self.start_date, '%d/%m/%Y'), STYLE_LINE_Data)

        if self.partner_ids:
            row += 1
            col = 0
            worksheet.write(row, col, _('العملاء'), TABLE_SUB_HEADER)
            col += 1
            worksheet.write(row, col, ' - '.join(self.partner_ids.mapped('name')), STYLE_LINE_Data)

        if self.stock_location_ids:
            row += 1
            col = 0
            worksheet.write(row, col, _('الفروع'), TABLE_SUB_HEADER)
            col += 1
            worksheet.write(row, col, ' - '.join(self.stock_location_ids.mapped('name')), STYLE_LINE_Data)
        if self.season_ids:
            row += 1
            col = 0
            worksheet.write(row, col, _('السيزون'), TABLE_SUB_HEADER)
            col += 1
            worksheet.write(row, col, ' - '.join(self.season_ids.mapped('name')), STYLE_LINE_Data)
        if self.category_ids:
            row += 1
            col = 0
            worksheet.write(row, col, _('نوع المنتج'), TABLE_SUB_HEADER)
            col += 1
            worksheet.write(row, col, ' - '.join(self.category_ids.mapped('name')), STYLE_LINE_Data)

        col = 0
        row += 1
        worksheet.write_merge(row, row + 1, col, col, _('الكود'), header_format)
        col += 1
        worksheet.write_merge(row, row + 1, col, col, _('رقم الصنف'), header_format)
        col += 1
        worksheet.write_merge(row, row + 1, col, col, _('الصنف'), header_format)
        col += 1
        worksheet.write_merge(row, row + 1, col, col, _('رصيد'), header_format)
        col += 1
        worksheet.write_merge(row, row + 1, col, col, _('سعر تكلفه'), header_format)
        col += 1
        worksheet.write_merge(row, row + 1, col, col, _('سعر مستهلك'), header_format)
        col += 1
        worksheet.write_merge(row, row + 1, col, col, _('القيمه بالتكلفه'), header_format)
        col += 1
        worksheet.write_merge(row, row + 1, col, col, _('القيمه بالمستهلك'), header_format)
        col += 1
        worksheet.write_merge(row, row + 1, col, col, _('تاريخ اخر شراء'), header_format)
        col += 1
        worksheet.write_merge(row, row + 1, col, col, _('تاريخ اخر بيع'), header_format)

        row += 1
        for i, record in enumerate(data):
            row += 1
            col = 0
            # worksheet.write(row, col, i + 1, STYLE_LINE_Data)
            # col += 1
            worksheet.write(row, col, record['product_barcode'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['product_code'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['product_name'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['aval_qty'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['standard_price'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['list_price'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['cost_price'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['sale_price'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['last_po_date'], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, record['last_so_date'], STYLE_LINE_Data)
        output = BytesIO()

        workbook.save(output)
        xls_file_path = (_('تقرير الرواكد.xls'))
        attachment_model = self.env['ir.attachment']
        attachment_model.search(
            [('res_model', '=', 'stock.product.slow.move'), ('res_id', '=', self.id)]).unlink()
        attachment_obj = attachment_model.create({
            'name': xls_file_path,
            'res_model': 'stock.product.slow.move',
            'res_id': self.id,
            'type': 'binary',
            'db_datas': base64.b64encode(output.getvalue()),
        })
        output.close()
        url = '/web/content/%s/%s' % (attachment_obj.id, xls_file_path)
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'new'}
