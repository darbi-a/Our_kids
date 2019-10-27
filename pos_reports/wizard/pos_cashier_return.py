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


class PosCashierReturn(models.TransientModel):
    _name = 'pos.cashier.return'
    _description = 'pos.cashier.return'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    branches_ids = fields.Many2many(comodel_name="pos.branch")
    type = fields.Selection(string="Report Type",default="xls", selection=[('xls', 'XLS'), ('pdf', 'PDF'), ], required=True, )

    def get_dates(self):
        start = self.date_from
        end = self.date_to
        dates = []
        current_start = start
        current_end = start + relativedelta(days=1)
        current_end = current_end if current_end < end else end

        while current_end <= end and current_start <= current_end:
            dates.append(current_start)
            current_start = current_end + relativedelta(days=1)
            current_end = start + relativedelta(days=1)
            current_end = current_end if current_end < end else end

        return dates

    def get_report_data(self):
        data = []
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Date from must be before date to!'))
        branch_ids = self.branches_ids.ids or self.env['pos.branch'].search([]).ids
        end_date = self.date_to
        end_time = datetime.max.time()
        end_date = datetime.combine(end_date, end_time)
        _sql_query = """
        select c.pos_branch_id,o.user_id,sum(l.price_subtotal_incl) as returned_incl,sum(l.price_subtotal) as returned,
        date_trunc('day',o.date_order) as o_date,o.name,o.pos_reference 
            from pos_order o
            join pos_order_line l on l.order_id = o.id
            join pos_session s on o.session_id = s.id
            join pos_config c on c.id = s.config_id
        where o.state in ('paid','done','invoiced') and o.date_order >= %s and  o.date_order <= %s and l.qty < 0
        and c.pos_branch_id in %s
        group by o_date,o.user_id,o.state,c.pos_branch_id,o.name,o.pos_reference
        order by o_date
        """
        self._cr.execute(_sql_query,(self.date_from,end_date,tuple(branch_ids)))
        for r in self._cr.fetchall():
            branch_id = r[0]
            user_id = r[1]
            returned_incl = r[2]
            returned = r[3]
            day = r[4]
            name = r[5]
            pos_reference = r[6]
            day_str = day.strftime('%Y/%m/%d')
            branch = self.env['pos.branch'].browse(branch_id)
            user = self.env['res.users'].browse(user_id)
            branch_name = branch.name
            data.append((day_str,name,pos_reference,user.name, branch_name, returned,returned_incl ))

        return data

    @api.multi
    def action_print_pdf(self):
        data = self.get_report_data()
        result={
            'data':data,
            'date_from':self.date_from,
            'date_to':self.date_to,
        }
        return self.env.ref('pos_reports.pos_cashier_return_report').report_action([], data=result)

    @api.multi
    def action_print_excel_file(self):
        self.ensure_one()
        data = self.get_report_data()
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

        worksheet = workbook.add_sheet(_('تقرير مرتجعات الكاشير'))
        lang = self.env.user.lang
        worksheet.cols_right_to_left = 1

        worksheet.col(0).width = 256 * 10
        worksheet.col(1).width = 256 * 50
        worksheet.col(2).width = 256 * 30
        row = 0
        col = 0
        worksheet.write_merge(row,row,col,col+3,_('تقرير مرتجعات الكاشير'),STYLE_LINE_Data)
        row += 1
        worksheet.write(row,col,_('التاريخ من'),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,str(self.date_from),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,_('التاريخ الى'),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,str(self.date_to),STYLE_LINE_Data)
        col += 1


        row += 2
        col = 0
        worksheet.write(row, col, _('التاريخ'), header_format)
        col += 1
        worksheet.write(row, col, _('رقم البون'), header_format)
        col += 1
        worksheet.write(row, col, _('رقم التسلسل'), header_format)
        col += 1
        worksheet.write(row, col, _('اسم الكاشير'), header_format)
        col += 1
        worksheet.write(row, col, _('الفرع'), header_format)
        col += 1
        worksheet.write(row, col, _('قيمة المرتجع'), header_format)
        col += 1
        for d in data:
            # month_sart = month[0]
            # # month_name = month_sart.strftime('%Y-%B')
            # month_name = format_date(date=month_sart, format='MMMM-y',locale='ar')
            row += 1
            col = 0
            worksheet.write(row, col, d[0], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, d[2], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, d[1], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, d[3], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, d[4], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, d[6], STYLE_LINE_Data)
            col += 1

        output = BytesIO()
        if data:
            workbook.save(output)
            xls_file_path = (_('تقرير مرتجعات الكاشير.xls'))
            attachment_model = self.env['ir.attachment']
            attachment_model.search([('res_model', '=', 'pos.cashier.return'), ('res_id', '=', self.id)]).unlink()
            attachment_obj = attachment_model.create({
                'name': xls_file_path,
                'res_model': 'pos.cashier.return',
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
                'res_model': 'pos.cashier.return',
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

