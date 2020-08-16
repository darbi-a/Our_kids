# -*- coding: utf-8 -*-
""" init object """
import pytz
import xlwt
import base64
from io import BytesIO
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


# def convert_date_to_local(date, tz):
#     local = pytz.timezone(tz)
#     date = date.replace(tzinfo=pytz.utc)
#     date = date.astimezone(local)
#     date.strftime('%Y-%m-%d: %H:%M:%S')
#     return date.replace(tzinfo=None)


class TotalsSaleCategWizard(models.TransientModel):
    _name = 'totals.sale_categ.wizard'
    _description = 'totals.sale_categ.wizard'

    def get_categ(self):
        categ_ids = self.env['product.category'].search([('parent_path', '!=', False)])
        categ_lst = []
        for cat in categ_ids:
            lst = cat.parent_path.split('/')
            if len(lst) > 1:
                if lst[1] != '' and int(lst[1]) not in categ_lst:
                    categ_lst.append(int(lst[1]))
        print("categ_lst == ", categ_lst)
        return [(6,0,categ_lst)]

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    branches_ids = fields.Many2many(comodel_name="pos.branch")
    season_ids = fields.Many2many(comodel_name="product.season", string="Seasons", )
    categ_ids = fields.Many2many(comodel_name="product.category",default=get_categ, string="Product Categories", )
    type = fields.Selection(string="Report Type",default="xls", selection=[('xls', 'XLS'), ('pdf', 'PDF'), ], required=True, )

    def get_dates(self):
        start = self.date_from
        end = self.date_to
        dates = []
        current_start = start
        current_end = start.replace(day=1) + relativedelta(months=1,days=-1)
        current_end = current_end if current_end < end else end

        while current_end <= end and current_start <= current_end:
            month_name = format_date(date=current_start, format='MMMM-y', locale='ar')
            dates.append((current_start,current_end,month_name))
            current_start = current_end + relativedelta(days=1)
            current_end = current_start.replace(day=1) + relativedelta(months=1,days=-1)
            current_end = current_end if current_end < end else end

        return dates



    def get_report_data(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Date from must be before date to!'))
        data = {}
        data2 = {}
        total = 0
        total_cash = 0
        total_bank = 0
        month_names = []
        branch_names = []
        # data['date_from'] = convert_date_to_local(self.date_from,self.env.user.tz)
        # data['date_from'] = convert_date_to_local(self.date_from,self.env.user.tz)
        data['date_from'] = self.date_from
        data['date_to'] = self.date_to
        monthes = self.get_dates()
        products = self.env['product.product'].sudo().search(['|', ('active', '=', True), ('active', '=', False)])

        if self.branches_ids:
            branches = self.branches_ids
        else:
            branches = self.env['pos.branch'].search([])
        if self.season_ids:
            seasons = self.season_ids.ids
        else:
            seasons = self.env['product.season'].search([]).ids
        if self.categ_ids:
            categ_ids =self.categ_ids
            categories = self.env['product.category'].sudo().search([('id', 'child_of', self.categ_ids.ids)])
        else:
            lst_ids = self.get_categ()
            if lst_ids:
                categ_ids = self.env['product.category'].sudo().browse(lst_ids[0][2])
                print("categ_ids",categ_ids)
                categories = self.env['product.category'].sudo().search([('id', 'child_of', categ_ids.ids)])
            else:
               lst_ids= self.env['product.category'].search([])
               categ_ids= lst_ids
               categories = self.env['product.category'].sudo().search([('id', 'child_of', categ_ids.ids)])

        for branch in branches:
            branch_names.append(branch.name)
            data.setdefault('branches',{})
            data['branches'].setdefault(branch.name,{})
            pos_lines = self.env['pos.order.line'].search([
                ('order_id.config_id.pos_branch_id', '=', branch.id),
                ('order_id.date_order', '>=', self.date_from),
                ('order_id.date_order', '<=', self.date_to),
                ])
            for cat in categ_ids:

                total_qty=0
                total_cost=0
                total_sale=0
                for line in pos_lines:
                    if line.product_id.categ_id.id in categories.ids :
                        if line.product_id.season_id:
                            if  line.product_id.season_id.id in seasons:
                                total_qty += self.get_rounding(line.qty)
                                total_sale += self.get_rounding(line.price_subtotal)
                                total_cost += self.get_rounding(line.qty * line.product_id.standard_price)
                        else:
                            total_qty += self.get_rounding(line.qty)
                            total_sale += self.get_rounding(line.price_subtotal)
                            total_cost += self.get_rounding(line.qty * line.product_id.standard_price)
                        print("line.product_id ",line.product_id.name)
                        print("product_id ",line.qty)
                        print("*****************",)
                data['branches'][branch.name][cat.name] = {
                    'total_qty': round(total_qty,2),
                    'total_sale': round(total_sale,2),
                    'total_cost': round(total_cost,2),
                }

        return data

    def get_rounding(self,num):

        lst = str(float(num)).split('.')
        num1 = lst[0]
        num2 = (lst[1])
        num3 = num2[0:2]
        number = num1 + '.' + num3
        return float(number)
    @api.multi
    def action_print_pdf(self):
        data = self.get_report_data()
        return self.env.ref('pos_reports.pos_totals_by_categ_report').report_action([], data=data)

    @api.multi
    def action_print_excel_file(self):
        self.ensure_one()
        data = self.get_report_data()
        print("Final Data => ",date)
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

        # for branch in data['branches']:
        date_from = data['date_from']
        date_to = data['date_to']
        worksheet = workbook.add_sheet(_('تقرير المبيعات بالاجماليات'))
        lang = self.env.user.lang
        if lang == "ar_SY":
            worksheet.cols_right_to_left = 1

        worksheet.col(0).width = 256 * 15
        worksheet.col(1).width = 256 * 20
        worksheet.col(3).width = 256 * 15
        worksheet.col(4).width = 256 * 15
        worksheet.col(5).width = 256 * 15
        row = 0
        col = 0
        worksheet.write_merge(row,row,col,col+3,_('إجمالي مبيعات الاقسام الرئيسية'),STYLE_LINE_Data)
        row += 1
        worksheet.write(row,col,_('التاريخ من'),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,str(data['date_from']),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,_('التاريخ الى'),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,str(data['date_to']),STYLE_LINE_Data)


        row += 2
        col = 0
        worksheet.write(row, col, _('الفرع'), header_format)
        col += 1
        worksheet.write(row, col, _('القسم'), header_format)
        col += 1
        worksheet.write(row, col, _('الكمية'), header_format)
        col += 1
        worksheet.write(row, col, _('اجمالي التكلفة بعد المرتجع'), header_format)
        col += 1
        worksheet.write(row, col, _('اجمالي المستهلك بعد الخصم'), header_format)
        col += 1
        branch_data = data['branches']


        for branch in branch_data:
            # month_sart = month[0]
            # # month_name = month_sart.strftime('%Y-%B')
            # month_name = format_date(date=month_sart, format='MMMM-y',locale='ar')
            row += 1
            col = 0
            total_qty=0
            total_cost=0
            total_sale=0
            worksheet.write(row, col, branch, STYLE_LINE_Data)

            for cat in branch_data[branch]:
                row += 1
                col = 1
                worksheet.write(row, col, cat, STYLE_LINE_Data)
                col += 1
                total_qty +=branch_data[branch][cat]['total_qty']
                worksheet.write(row, col, branch_data[branch][cat]['total_qty'], STYLE_LINE_Data)
                col += 1
                total_cost += branch_data[branch][cat]['total_cost']
                worksheet.write(row, col, branch_data[branch][cat]['total_cost'], STYLE_LINE_Data)
                col += 1
                total_sale += branch_data[branch][cat]['total_sale']
                worksheet.write(row, col, branch_data[branch][cat]['total_sale'], STYLE_LINE_Data)
                col += 1

            row += 1
            col = 1
            worksheet.write(row, col, 'Total', TABLE_HEADER_batch)
            col += 1
            worksheet.write(row, col, total_qty, TABLE_HEADER_batch)
            col += 1
            worksheet.write(row, col, total_cost, TABLE_HEADER_batch)
            col += 1
            worksheet.write(row, col, total_sale, TABLE_HEADER_batch)
            col += 1


        output = BytesIO()


        if data:
            workbook.save(output)
            xls_file_path = (_('تقريرإجمالي مبيعات الاقسام.xls'))
            attachment_model = self.env['ir.attachment']
            attachment_model.search([('res_model', '=', 'totals.sale_categ.wizard'), ('res_id', '=', self.id)]).unlink()
            attachment_obj = attachment_model.create({
                'name': xls_file_path,
                'res_model': 'totals.sale_categ.wizard',
                'res_id': self.id,
                'type': 'binary',
                'db_datas': base64.b64encode(output.getvalue()),
            })

            # Close the String Stream after saving it in the attachments
            output.close()
            url = '/web/content/%s/%s' % (attachment_obj.id,   xls_file_path)
            return {'type': 'ir.actions.act_url', 'url': url, 'target': 'new'}

        else:

            view_action = {
                'name': _(' Print Sales Persons Report'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'totals.sale_categ.wizard',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new',
                'context': self.env.context,
            }

            return view_action

    def action_print(self):
        if self.type == 'xls':
            return self.action_print_excel_file()

        elif self.type == 'pdf':
            return self.action_print_pdf()

