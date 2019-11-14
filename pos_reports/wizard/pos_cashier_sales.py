# -*- coding: utf-8 -*-
""" init object """
import pytz
import xlwt
import base64
from io import BytesIO
from psycopg2.extensions import AsIs
from babel.dates import format_date, format_datetime, format_time
from odoo import fields, models, api, _, tools, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date, timedelta
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


class PosCashierSales(models.TransientModel):
    _name = 'pos.cashier.sales'
    _description = 'pos.cashier.sales'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    branches_ids = fields.Many2many(comodel_name="pos.branch")
    type = fields.Selection(string="Report Type", default="xls", selection=[('xls', 'XLS'), ('pdf', 'PDF'), ],
                            required=True, )

    def get_returns_count(self):
        start = self.date_from
        end = self.date_to
        data = {}
        current_start = start

        while current_start <= end :
            # dates.append(current_start)
            branches = self.branches_ids or self.env['pos.branch'].search([])
            end_time = datetime.max.time()
            end_date = datetime.combine(current_start, end_time)
            day_str = current_start.strftime('%Y/%m/%d')

            # for branch in branches:
            orders = self.env['pos.order'].search(
                [('session_id.stop_at', '>=', current_start), ('session_id.stop_at', '<=', end_date),('config_id.pos_branch_id','in',branches.ids)])
            return_lines = orders.mapped('lines').filtered(lambda l:l.qty <= 0)
            return_orders = return_lines.mapped('order_id')
            non_return_orders = orders - return_orders
            # branch_name = branch.name
            data.setdefault(day_str, {})
            # data[day_str].setdefault(branch_name, {})
            data[day_str].setdefault('return', 0)
            data[day_str].setdefault('normal', 0)
            data[day_str]['return'] += len(return_orders)
            data[day_str]['normal'] += len(non_return_orders)
            current_start = current_start + relativedelta(days=1)

        return data

    def get_loss_gain(self):
        data = []
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Date from must be before date to!'))
        branch_ids = self.branches_ids.ids or self.env['pos.branch'].search([]).ids
        end_date = self.date_to
        end_time = datetime.max.time()
        end_date = datetime.combine(end_date, end_time)
        _sql_query = """
         select c.pos_branch_id as branch_id,s.user_id,date_trunc('day',stop_at) as stop ,
         sum(CASE when stl.amount < 0 THEN -1*stl.amount END) as loss,
         sum(CASE when stl.amount > 0 THEN stl.amount END) as gain
            from pos_session s
            join account_bank_statement st on s.id = st.pos_session_id
            join account_bank_statement_line stl on st.id = stl.statement_id
            join pos_config c on s.config_id = c.id
        where s.state = 'closed' and s.stop_at >= %s and  s.stop_at <= %s 
        and stl.pos_statement_id is NULL and stl.ref is NULL and c.pos_branch_id in %s
        group by stop,s.user_id,branch_id
        order by branch_id,stop,s.user_id
        """
        self._cr.execute(_sql_query, (self.date_from, end_date, tuple(branch_ids)))
        for r in self._cr.fetchall():
            data.append(r)

        return data

    def get_report_data(self):
        data = {}
        visas = set()
        totals = {}
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Date from must be before date to!'))
        branch_ids = self.branches_ids.ids or self.env['pos.branch'].search([]).ids
        end_date = self.date_to
        end_time = datetime.max.time()
        end_date = datetime.combine(end_date, end_time)
        _sql_query = """
        select c.pos_branch_id as branch_id,st.journal_id,s.user_id,sum(stl.amount) as amount,date_trunc('day',stop_at) as stop 
            from pos_session s
            join account_bank_statement st on s.id = st.pos_session_id
            join account_bank_statement_line stl on st.id = stl.statement_id
            join pos_config c on s.config_id = c.id
        where s.state = 'closed' and s.stop_at >= %s and  s.stop_at <= %s and stl.pos_statement_id is not NULL and c.pos_branch_id in %s
        group by stop,s.user_id,branch_id,st.journal_id
        order by stop
        """
        self._cr.execute(_sql_query, (self.date_from, end_date, tuple(branch_ids)))
        for r in self._cr.fetchall():
            branch_id = r[0]
            journal_id = r[1]
            user_id = r[2]
            amount = r[3]
            day = r[4]

            branch = self.env['pos.branch'].browse(branch_id)
            user = self.env['res.users'].browse(user_id)
            branch_name = branch.name
            user_name = user.name
            day_str = day.strftime('%Y/%m/%d')
            self.set_defaults(day_str,branch_name,user_name,data,totals)
            current_dic = data[day_str][branch_name][user_name]

            journal = self.env['account.journal'].browse(journal_id)
            if journal.type == 'bank':
                journal_name = journal.name
                current_dic['total_visa'] += amount
                current_dic['visas'][journal_name] = amount

                totals[day_str].setdefault(journal_name, 0)
                totals[day_str][journal_name] += amount
                totals[day_str]['total_visa'] += amount
                visas |= set([journal_name])
            elif journal.type == 'cash':
                current_dic['total_cash'] += amount

                totals[day_str]['cash'] += amount
        dates = list(set(data.keys()))
        dates.sort(key=lambda d: d)
        los_gain_data = self.get_loss_gain()
        return_data = self.get_returns_count()
        for r in los_gain_data:
            branch_id = r[0]
            user_id = r[1]
            day = r[2]
            loss = r[3] or 0
            gain = r[4] or 0
            day_str = day.strftime('%Y/%m/%d')
            branch = self.env['pos.branch'].browse(branch_id)
            user = self.env['res.users'].browse(user_id)
            branch_name = branch.name
            user_name = user.name
            self.set_defaults(day_str, branch_name, user_name, data, totals)
            data[day_str][branch_name][user_name]['gain'] = gain
            data[day_str][branch_name][user_name]['loss'] = loss
            totals[day_str]['gain'] += gain
            totals[day_str]['loss'] += loss

        return data, list(visas), totals, dates , return_data

    def set_defaults(self,day_str,branch_name,user_name,data_dict,total_data):

        data_dict.setdefault(day_str, {})
        data_dict[day_str].setdefault(branch_name, {})
        data_dict[day_str][branch_name].setdefault(user_name, {})
        current_dic = data_dict[day_str][branch_name][user_name]
        current_dic.setdefault('total_visa', 0)
        current_dic.setdefault('total_cash', 0)
        current_dic.setdefault('visas', {})

        total_data.setdefault(day_str, {})
        # total_data[day_str].setdefault(branch_name, {})
        total_data[day_str].setdefault('cash', 0)
        total_data[day_str].setdefault('total_visa', 0)
        total_data[day_str].setdefault('loss', 0)
        total_data[day_str].setdefault('gain', 0)

    @api.multi
    def action_print_excel_file(self):
        self.ensure_one()
        data, visas, totals, dates , return_data = self.get_report_data()
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

        worksheet = workbook.add_sheet(_('تتقرير مبيعات الكاشير بالفروع'))
        lang = self.env.user.lang
        worksheet.cols_right_to_left = 1

        worksheet.col(0).width = 256 * 10
        worksheet.col(1).width = 256 * 50
        worksheet.col(2).width = 256 * 30
        row = 0
        col = 0
        worksheet.write_merge(row, row, col, col + 3, _('تقرير مبيعات الكاشير بالفروع'), STYLE_LINE_Data)
        row += 1
        worksheet.write(row, col, _('التاريخ من'), STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col, str(self.date_from), STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col, _('التاريخ الى'), STYLE_LINE_Data)
        col += 1
        worksheet.write(row, col, str(self.date_to), STYLE_LINE_Data)
        visas_len = len(visas)
        row += 2
        for day in dates:
            col = 0
            row += 2
            worksheet.write_merge(row, row + 1, col, col, _('التاريخ'), header_format)
            col += 1
            worksheet.write_merge(row, row + 1, col, col, _('الفرع'), header_format)
            col += 1
            worksheet.write_merge(row, row + 1, col, col, _('اسم الكاشير'), header_format)
            col += 1
            worksheet.write_merge(row, row + 1, col, col, _('المقبوضات النقدية'), header_format)
            col += 1
            if visas_len:
                worksheet.write_merge(row, row, col, col + visas_len - 1, _('الفيزا'), header_format)
                col += visas_len
            worksheet.write_merge(row, row + 1, col, col, _('اجمالى الفيزا'), header_format)
            col += 1
            worksheet.write_merge(row, row + 1, col, col, _('العجز'), header_format)
            col += 1
            worksheet.write_merge(row, row + 1, col, col, _('الزيادة'), header_format)
            col += 1
            worksheet.write_merge(row, row + 1, col, col, _('اجمالى المبيعات'), header_format)
            col += 1
            row += 1
            col = 3
            for v in visas:
                col += 1
                worksheet.write(row, col, v, header_format)

            for branch in data[day]:

                for user in data[day][branch]:
                    user_data = data[day][branch][user]
                    user_visa = user_data['visas']
                    cash = user_data.get('total_cash') or 0.0
                    visa = user_data.get('total_visa') or 0.0
                    gain = user_data.get('gain') or 0.0
                    loss = user_data.get('loss') or 0.0
                    total = cash + visa
                    col = 0
                    row += 1
                    worksheet.write(row, col, day, STYLE_LINE_Data)
                    col += 1
                    worksheet.write(row, col, branch, STYLE_LINE_Data)
                    col += 1
                    worksheet.write(row, col, user, STYLE_LINE_Data)
                    col += 1
                    worksheet.write(row, col, user_data.get('total_cash') or 0.0, STYLE_LINE_Data)
                    for v in visas:
                        col += 1
                        worksheet.write(row, col, user_visa.get(v) or 0.0, STYLE_LINE_Data)

                    col += 1
                    worksheet.write(row, col, user_data.get('total_visa') or 0.0, STYLE_LINE_Data)
                    col += 1
                    worksheet.write(row, col, loss, STYLE_LINE_Data)
                    col += 1
                    worksheet.write(row, col, gain, STYLE_LINE_Data)
                    col += 1
                    worksheet.write(row, col, total, STYLE_LINE_Data)

            row += 1
            col = 0
            total_visa = totals[day].get('total_visa', 0.0)
            total_cash = totals[day].get('cash', 0.0)
            total_loss = totals[day].get('loss', 0.0)
            total_gain = totals[day].get('gain', 0.0)
            total_amount = total_visa + total_cash
            # worksheet.write(row, col, _('الاجمالي'), STYLE_LINE_Data)
            # col += 1
            worksheet.write_merge(row, row, col, col + 2,  'الاجمالي ', STYLE_LINE_Data)
            col += 3
            worksheet.write(row, col, totals[day].get('cash', 0.0), STYLE_LINE_Data)
            for v in visas:
                col += 1
                worksheet.write(row, col, totals[day].get(v, 0.0), STYLE_LINE_Data)

            col += 1
            worksheet.write(row, col, total_visa, STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, total_loss, STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, total_gain, STYLE_LINE_Data)
            col += 1
            worksheet.write(row, col, total_amount, STYLE_LINE_Data)

            width = col - 1
            col = 0
            row += 1
            worksheet.write_merge(row,row, col,col + width, _('عدد اوردرات المبيعات'), STYLE_LINE_Data)
            col += width + 1
            worksheet.write(row, col, return_data.get(day,{}).get('normal',0), STYLE_LINE_Data)
            col = 0
            row += 1
            worksheet.write_merge(row,row, col,col + width, _('عدد الاوردرات المرتجعة'), STYLE_LINE_Data)
            col += width + 1
            worksheet.write(row, col, return_data.get(day,{}).get('return',0), STYLE_LINE_Data)
            row += 2

        output = BytesIO()
        if data:
            workbook.save(output)
            xls_file_path = (_('تقرير مبيعات الكاشير بالفروع.xls'))
            attachment_model = self.env['ir.attachment']
            attachment_model.search([('res_model', '=', 'pos.cashier.sales'), ('res_id', '=', self.id)]).unlink()
            attachment_obj = attachment_model.create({
                'name': xls_file_path,
                'res_model': 'pos.cashier.sales',
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
                'name': _(' Print Sales Persons Report'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.cashier.sales',
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'target': 'new',
                'context': self.env.context,
            }

            return view_action

    @api.multi
    def action_print_pdf(self):
        data, visas, totals, dates, return_data = self.get_report_data()
        result = {
            'data': data,
            'visas': visas,
            'totals': totals,
            'dates': dates,
            'return_data': return_data,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return self.env.ref('pos_reports.pos_cashier_sales_report').report_action([], data=result)

    def action_print(self):
        if self.type == 'xls':
            return self.action_print_excel_file()

        elif self.type == 'pdf':
            return self.action_print_pdf()
