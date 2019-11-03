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


class TotalsReportWizard(models.TransientModel):
    _name = 'totals.report.wizard'
    _description = 'totals.report.wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    branches_ids = fields.Many2many(comodel_name="pos.branch")
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
        total = 0
        total_cash = 0
        total_bank = 0
        month_names = []
        # data['date_from'] = convert_date_to_local(self.date_from,self.env.user.tz)
        # data['date_from'] = convert_date_to_local(self.date_from,self.env.user.tz)
        data['date_from'] = self.date_from
        data['date_to'] = self.date_to
        monthes = self.get_dates()
        if self.branches_ids:
            branches = self.branches_ids
        else:
            branches = self.env['pos.branch'].search([])

        # for branch in branches:
        data.setdefault('branches',{})
        # data['branches'].setdefault(branch.name,{})
        for month in monthes:
            start_month = month[0]
            end_month = month[1]
            month_name = month[2]
            # month_name = month_sart.strftime('%Y-%B')
            pos_sessions = self.env['pos.session'].search([
                ('state', '=', 'closed'),
                ('config_id.pos_branch_id', 'in', branches.ids),
                ('stop_at', '<=', end_month),
                ('stop_at', '>=', start_month)])

            statements = pos_sessions.mapped('statement_ids')
            cash_statements = statements.filtered(lambda x: x.journal_id.type == 'cash')
            bank_statements = statements.filtered(lambda x: x.journal_id.type == 'bank')
            cash = sum(cash_statements.mapped('line_ids').filtered(lambda l:l.pos_statement_id.id != False).mapped('amount'))
            bank = sum(bank_statements.mapped('line_ids').filtered(lambda l:l.pos_statement_id.id != False).mapped('amount'))
            total_amount = cash + bank
            total_cash += cash
            total_bank += bank
            total += total_amount
            # data['branches'][branch.name][month_name] = {
            data['branches'][month_name] = {
                'cash': cash,
                'bank': bank,
                'total_amount': total_amount,
            }
        for month in monthes:
            month_names.append(month[2])
        data['monthes'] = month_names
        branch_names = ' - '.join(branches.mapped('name'))
        data['branch_names'] = branch_names
        return data

    @api.multi
    def action_print_pdf(self):
        data = self.get_report_data()
        return self.env.ref('pos_reports.pos_totals_report').report_action([], data=data)

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

        # for branch in data['branches']:
        date_from = data['date_from']
        date_to = data['date_to']
        worksheet = workbook.add_sheet(_('تقرير المبيعات بالاجماليات'))
        lang = self.env.user.lang
        if lang == "ar_SY":
            worksheet.cols_right_to_left = 1

        worksheet.col(0).width = 256 * 10
        worksheet.col(1).width = 256 * 50
        worksheet.col(2).width = 256 * 30
        row = 0
        col = 0
        worksheet.write_merge(row,row,col,col+3,_('تقرير مبيعات عام بالاجماليات'),STYLE_LINE_Data)
        row += 1
        worksheet.write(row,col,_('التاريخ من'),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,str(data['date_from']),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,_('التاريخ الى'),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,str(data['date_to']),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,_('الفرع'),STYLE_LINE_Data)
        col += 1
        worksheet.write(row,col,data['branch_names'],STYLE_LINE_Data)
        col += 1

        row += 2
        col = 0
        worksheet.write(row, col, _('الشهر'), header_format)
        col += 1
        worksheet.write(row, col, _('النقدى'), header_format)
        col += 1
        worksheet.write(row, col, _('الفيزا'), header_format)
        col += 1
        worksheet.write(row, col, _('الاجمالى'), header_format)
        col += 1
        branch_data = data['branches']
        total_amount = 0
        total_bank = 0
        total_cash = 0
        for month in data['monthes']:
            # month_sart = month[0]
            # # month_name = month_sart.strftime('%Y-%B')
            # month_name = format_date(date=month_sart, format='MMMM-y',locale='ar')
            row += 1
            col = 0
            worksheet.write(row, col, month, STYLE_LINE_Data)
            col += 1
            total_cash += branch_data[month]['cash']
            worksheet.write(row, col, branch_data[month]['cash'], STYLE_LINE_Data)
            col += 1
            total_bank += branch_data[month]['bank']
            worksheet.write(row, col, branch_data[month]['bank'], STYLE_LINE_Data)
            col += 1
            total_amount += branch_data[month]['total_amount']
            worksheet.write(row, col, branch_data[month]['total_amount'], STYLE_LINE_Data)
            col += 1

        row += 1
        col = 0
        worksheet.write(row,col,_('الاجمالي'),STYLE_LINE_Data)
        worksheet.write(row,col+1,total_cash,STYLE_LINE_Data)
        worksheet.write(row,col+2,total_bank,STYLE_LINE_Data)
        worksheet.write(row,col+3,total_amount,STYLE_LINE_Data)

        output = BytesIO()


        if data:
            workbook.save(output)
            xls_file_path = (_('تقرير المبيعات بالاجماليات.xls'))
            attachment_model = self.env['ir.attachment']
            attachment_model.search([('res_model', '=', 'totals.report.wizard'), ('res_id', '=', self.id)]).unlink()
            attachment_obj = attachment_model.create({
                'name': xls_file_path,
                'res_model': 'totals.report.wizard',
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
                'res_model': 'totals.report.wizard',
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

