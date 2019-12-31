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


class PosLosGain(models.TransientModel):
    _name = 'pos.loss.gain'
    _description = 'pos.loss.gain'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    branches_ids = fields.Many2many(comodel_name="pos.branch")
    type = fields.Selection(string="Report Type",default="xls", selection=[('xls', 'XLS'), ('pdf', 'PDF'), ], required=True, )


    def get_report_data(self):
        data = []
        totals = {
            'loss': 0,
            'gain': 0,
            'total': 0,
        }
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Date from must be before date to!'))
        branches = self.branches_ids or self.env['pos.branch'].search([])
        branch_ids = branches.ids
        end_date = self.date_to
        end_time = datetime.max.time()
        end_date = datetime.combine(end_date, end_time)
        for pranch in branches:
            _sql_query = """
            select s.user_id,date_trunc('day',stop_at) as stop,
             sum(CASE when stl.amount < 0 THEN -1*stl.amount END) as loss,
             sum(CASE when stl.amount > 0 THEN stl.amount END) as gain
                from pos_session s
                join account_bank_statement st on s.id = st.pos_session_id
                join account_bank_statement_line stl on st.id = stl.statement_id
                join pos_config c on s.config_id = c.id
            where s.state = 'closed' and s.stop_at >= %s and  s.stop_at <= %s 
            and stl.pos_statement_id is NULL and stl.ref is NULL and c.pos_branch_id = %s
            group by stop,s.user_id
            order by stop,s.user_id
            """
            self._cr.execute(_sql_query,(self.date_from,end_date,pranch.id))
            # print('self._cr.fetchall() -', self._cr.fetchall())
            for r in self._cr.fetchall():
                # branch_id = r[0]
                user_id = r[0]
                day = r[1]
                loss = r[2] or 0.0
                gain = r[3] or 0.0
                day_str = day.strftime('%Y/%m/%d')
                # branch = self.env['pos.branch'].browse(branch_id)
                user = self.env['res.users'].browse(user_id)
                branch_name = pranch.name
                # data.setdefault(branch_name,[])
                # gain = difference if difference > 0 else 0
                # loss = difference if difference < 0 else 0
                data.append((day_str,user.name, gain, loss,branch_name ))
                totals['loss'] += loss
                totals['gain'] += gain
                totals['total'] += gain - loss
        branch_names = ' - '.join(branches.mapped('name'))
        return data,totals,branch_names

    @api.multi
    def action_print_pdf(self):
        data,totals,branch_names = self.get_report_data()
        result={
            'branches':data,
            'totals':totals,
            'date_from':self.date_from,
            'date_to':self.date_to,
            'branch_names':branch_names
        }
        return self.env.ref('pos_reports.pos_los_gain_report').report_action([], data=result)

    @api.multi
    def action_print_excel_file(self):
        self.ensure_one()
        data,totals,branch_names = self.get_report_data()
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

        # for branch in data:
        worksheet = workbook.add_sheet(_('تقرير ارباح وخسائر بالكاشير'))
        lang = self.env.user.lang
        if lang == "ar_SY":
            worksheet.cols_right_to_left = 1

        worksheet.col(0).width = 256 * 10
        worksheet.col(1).width = 256 * 50
        worksheet.col(2).width = 256 * 30
        row = 0
        col = 0
        worksheet.write_merge(row,row,col,col+3,_('تقرير ارباح وخسائر بالكاشير'),STYLE_LINE_Data)
        row += 1
        worksheet.write(row,col,_('التاريخ من'),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,str(self.date_from),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,_('التاريخ الى'),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,str(self.date_to),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,_('الفرع'),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,branch_names,STYLE_LINE_Data)
        col += 1

        row += 2
        col = 0
        worksheet.write(row, col, _('التاريخ'), header_format)
        col += 1
        worksheet.write(row, col, _('اسم الكاشير'), header_format)
        col += 1
        worksheet.write(row, col, _('العجز'), header_format)
        col += 1
        worksheet.write(row, col, _('الزيادة'), header_format)
        col += 1
        worksheet.write(row, col, _('الاجمالي'), header_format)
        col += 1
        # branch_data = data[branch]
        branch_data = data
        for d in branch_data:
            # month_sart = month[0]
            # # month_name = month_sart.strftime('%Y-%B')
            # month_name = format_date(date=month_sart, format='MMMM-y',locale='ar')
            row += 1
            col = 0
            worksheet.write(row, col, d[0], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, d[1], STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, abs(d[3]), STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, abs(d[2]), STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, d[2] - d[3], STYLE_LINE_Data)
            col += 1

        col = 0
        row += 1
        worksheet.write_merge(row, row, col,  col+1, _('الاجمالي'), STYLE_LINE_Data)
        col += 2
        worksheet.write(row, col, totals['loss'], STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col, totals['gain'], STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col, totals['total'], STYLE_LINE_Data)


        output = BytesIO()
        if data:
            workbook.save(output)
            xls_file_path = (_('تقرير عجز وزيادة الكاشير.xls'))
            attachment_model = self.env['ir.attachment']
            attachment_model.search([('res_model', '=', 'pos.loss.gain'), ('res_id', '=', self.id)]).unlink()
            attachment_obj = attachment_model.create({
                'name': xls_file_path,
                'res_model': 'pos.loss.gain',
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
                'res_model': 'pos.loss.gain',
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

