# -*- coding: utf-8 -*-
""" init object """
import pytz
import xlwt
import base64
from io import BytesIO
from psycopg2.extensions import AsIs
from babel.dates import format_date, format_datetime, format_time
from odoo import fields, models, api, _ ,tools, SUPERUSER_ID
from odoo.exceptions import ValidationError,UserError
from datetime import datetime , date ,timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta
from odoo.fields import Datetime as fieldsDatetime
import calendar
from odoo import http
from odoo.http import request
from odoo import tools

import logging

LOGGER = logging.getLogger(__name__)


class InventoryValuationReportVendor(models.TransientModel):
    _name = 'inventory.valuation.report.wizard'
    _description = 'inventory.valuation.report.wizard'

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            self.warehouse_ids = False

    date_to = fields.Date(required=True)
    date_from = fields.Date(required=True)
    company_id = fields.Many2one(comodel_name="res.company",default= lambda x:x.env.user.company_id, required=True)
    type = fields.Selection(string="Report Type",default="xls", selection=[('xls', 'XLS'), ('pdf', 'PDF'), ], required=True, )
    partner_ids = fields.Many2many(comodel_name="res.partner", string="Vendors")
    tag_ids = fields.Many2many(comodel_name="res.partner.category", string="Tags", )
    warehouse_ids = fields.Many2many(comodel_name="stock.warehouse")
    season_ids = fields.Many2many(comodel_name="product.season", )

    @api.model
    def get_location(self, warehouse):
        stock_ids = []
        location_obj = self.env['stock.location']
        domain = [('company_id', '=', self.company_id.id), ('usage', '=', 'internal')]
        stock_ids.append(warehouse.view_location_id.id)
        domain.append(('location_id', 'child_of', stock_ids))
        final_stock_ids = location_obj.search(domain).ids
        return final_stock_ids

    @api.model
    def get_valuation(self, product, warehouse):
        value = 0.0
        locations = self.get_location(warehouse)
        lst_moves = self.env['stock.move'].search([('product_id', '=', product.id),('state', '=', 'done'),'|',('location_id', 'in', locations),('location_dest_id', 'in', locations)])
        for mov in lst_moves:
            value += mov.value
        return value

    def get_report_data(self):
        data = {}
        products_domain = ['|',('active','=',True),('active','=',False)]
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Date from must be before date to'))
        if self.partner_ids and self.tag_ids:
            raise ValidationError(_('You have to select either partners or tags!'))
        # end_time = datetime.max.time()
        # start_date = datetime.combine(start, end_time)
        partners = self.env['res.partner']
        if self.partner_ids:
            partners = self.partner_ids
        elif self.tag_ids:
            partners = partners.search([('category_id','in',self.tag_ids.ids)])
        else:
            partners = partners.search([])

        if self.warehouse_ids:
            warehouses = self.warehouse_ids
        else:
            warehouses = self.env['stock.warehouse'].search([('company_id','=',self.company_id.id)])

        if self.season_ids:
            products = self.env['product.product'].search( products_domain + [('season_id','in',self.season_ids.ids)])
        else:
            products = self.env['product.product'].search(products_domain)

        for partner in partners:
            # partner_products = products.filtered(lambda p:p.vendor_num == partner.vendor_num)
            supplier_info = self.env['product.supplierinfo'].search([('name','=',partner.id)])
            partner_products = products.filtered(lambda p:p.variant_seller_ids in supplier_info)
            data.setdefault(partner.name,{})
            for product in partner_products:
                # data[partner].setdefault(product,{})
                data[partner.name][product.display_name] = {
                    'barcode': product.barcode,
                    'categ': product.categ_id.name ,
                    'season': product.season_id.name,
                    'qty': product.with_context(to_date=self.date_to,company_owned=True).qty_available,
                    'cost': product.with_context(to_date=self.date_to).stock_value,
                    'sale_price': product.list_price,
                }
                for warehouse in warehouses:
                    qty = product.with_context(warehouse=warehouse.id,to_date=self.date_to).qty_available
                    # evaluation = self.get_valuation(product,warehouse)
                    data[partner.name][product.display_name][warehouse.name] = {
                        'qty':qty,
                        # 'evaluation': evaluation,
                        'evaluation': qty * product.standard_price,
                    }

        return data,warehouses

    @api.multi
    def action_print_excel_file(self):
        self.ensure_one()
        data,warehouses = self.get_report_data()
        workbook = xlwt.Workbook()
        TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, color-index black,height 160;'
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
            'font: bold 1, name Aharoni , color-index black,height 160;'
            'align: vertical center, horizontal center, wrap off;'
            'alignment: wrap 1;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour gray25, pattern_back_colour gray25'
        )
        TABLE_HEADER_payslib = xlwt.easyxf(
            'font: bold 1, name Tahoma, color-index black,height 160;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour silver_ega, pattern_back_colour silver_ega'
        )
        TABLE_HEADER_Data = TABLE_HEADER
        TABLE_HEADER_Data.num_format_str = '#,##0.00_);(#,##0.00)'
        STYLE_LINE = xlwt.easyxf(
            'align: vertical center, horizontal center, wrap off;',
            'borders: left thin, right thin, top thin, bottom thin; '
            # 'num_format_str: General'
        )
        STYLE_Description_LINE = xlwt.easyxf(
            'align: vertical center, horizontal left, wrap 1;',
            'borders: left thin, right thin, top thin, bottom thin;'
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

        worksheet = workbook.add_sheet(_('تقرير تقييم المخزون'))
        lang = self.env.user.lang
        worksheet.cols_right_to_left = 1

        row = 0
        col = 0
        worksheet.write_merge(row, row, col, col + 3, _('تقرير تقييم المخزون'), STYLE_LINE_Data)
        row += 1
        worksheet.write(row, col, _('التاريخ من'), STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col,datetime.strftime(self.date_from, '%d/%m/%Y') , STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col, _('التاريخ الى'), STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col,datetime.strftime(self.date_to, '%d/%m/%Y') , STYLE_LINE_Data)
        col += 1
        if self.tag_ids:
            worksheet.write(row, col, _('نوع الموردين'), STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, ' - '.join(self.tag_ids.mapped('name')), STYLE_LINE_Data)

        row += 2
        col = 0
        worksheet.write_merge(row,row+1,col,col,_('اسم المورد'),header_format)
        col += 1
        worksheet.write_merge(row,row+1,col,col,_('تصنيف المنتج'),header_format)
        col += 1
        worksheet.write_merge(row,row+1,col,col,_('باركود'),header_format)
        col += 1
        worksheet.write_merge(row,row+1,col,col,_('الموسم'),header_format)
        col += 1
        worksheet.write_merge(row,row+1,col,col,_('اسم المنتج'),header_format)
        col += 1
        worksheet.write_merge(row,row+1,col,col,_('الكمية المتوفرة'),header_format)
        col += 1
        worksheet.write_merge(row,row+1,col,col,_('سعر البيع'),header_format)
        col += 1
        worksheet.write_merge(row,row+1,col,col,_('اجمالي القيمة'),header_format)
        col += 1

        for wh in warehouses:
            worksheet.write_merge(row, row, col, col+1, wh.name, header_format)
            worksheet.write(row+1,col,_('الكمية'),header_format)
            worksheet.write(row+1,col+1,_('القيمة'),header_format)
            col += 2

        row += 2
        for partner in data:
            for product in data[partner]:
                product_data = data[partner][product]
                col = 0
                worksheet.write(row,col,partner,STYLE_LINE_Data)
                col += 1
                worksheet.write(row,col,product_data['categ'],STYLE_LINE_Data)
                col += 1
                worksheet.write(row,col,product_data['barcode'],STYLE_LINE_Data)
                col += 1
                worksheet.write(row,col,product_data['season'],STYLE_LINE_Data)
                col += 1
                worksheet.write(row,col,product,STYLE_LINE_Data)
                col += 1
                worksheet.write(row,col,product_data['qty'],STYLE_LINE_Data)
                col += 1
                worksheet.write(row,col,product_data['sale_price'],STYLE_LINE_Data)
                col += 1
                worksheet.write(row,col,product_data['cost'],STYLE_LINE_Data)
                col += 1

                for wh in warehouses:
                    worksheet.write(row, col, product_data[wh.name]['qty'], STYLE_LINE_Data)
                    col += 1
                    worksheet.write(row, col, product_data[wh.name]['evaluation'], STYLE_LINE_Data)
                    col += 1

                row += 1

        output = BytesIO()
        if data:
            workbook.save(output)
            xls_file_path = (_('تقرير تقييم المخزون.xls'))
            attachment_model = self.env['ir.attachment']
            attachment_model.search([('res_model', '=', 'inventory.valuation.report.wizard'), ('res_id', '=', self.id)]).unlink()
            attachment_obj = attachment_model.create({
                'name': xls_file_path,
                'res_model': 'inventory.valuation.report.wizard',
                'res_id': self.id,
                'type': 'binary',
                'db_datas': base64.b64encode(output.getvalue()),
            })

            # Close the String Stream after saving it in the attachments
            output.close()
            url = '/web/content/%s/%s' % (attachment_obj.id, xls_file_path)
            return {'type': 'ir.actions.act_url', 'url': url, 'target': 'new'}

        else:

            view_action = {
                'name': _(' Vendor Balance Report'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'inventory.valuation.report.wizard',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new',
                'context': self.env.context,
            }

            return view_action


    @api.multi
    def action_print_pdf(self):
        data,warehouses = self.get_report_data()
        result={
            'data':data,
            'warehouses':warehouses.mapped('name'),
            'date_from':datetime.strftime(self.date_from, '%d/%m/%Y'),
            'date_to':datetime.strftime(self.date_to, '%d/%m/%Y'),
            'tags': ' - '.join(self.tag_ids.mapped('name')),
        }
        return self.env.ref('inventory_valuation_report_vendor.inventory_evaluation_report').report_action(self, data=result)



    def action_print(self):
        if self.type == 'xls':
            return self.action_print_excel_file()

        elif self.type == 'pdf':
            return self.action_print_pdf()

