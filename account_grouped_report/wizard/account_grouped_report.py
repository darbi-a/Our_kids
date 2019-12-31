# -*- coding: utf-8 -*-
""" init object """

import xlwt
import base64
from io import BytesIO

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError,UserError

import logging

LOGGER = logging.getLogger(__name__)

class AccountGroupedReport(models.TransientModel):
    _name = 'account.grouped.report'

    date_from = fields.Date()
    date_to = fields.Date()
    account_group_ids = fields.Many2many(comodel_name="account.group",required=True)

    def add_group_to_data(self,p_group,data_dict,_where):
        accounts = self.env['account.account'].search([('group_id', '=', p_group.id)])
        child_group = self.env['account.group'].search([('parent_id', '=', p_group.id)])
        data_dict[p_group] = {
            'debit': 0,
            'credit': 0,
            'balance': 0,
            'start_balance': 0,
            'accounts': [],
            'child_groups': {},
        }
        current_dict = data_dict[p_group]
        for account in accounts:
            sql_query = "SELECT account_id, sum(debit) as debit, sum(credit) as credit from account_move_line where account_id = %s %s group by account_id " % (
            account.id, _where)
            self._cr.execute(sql_query)
            r = self._cr.fetchone()
            debit = r and r[1] or 0
            credit = r and r[2] or 0
            balance = r and (debit - credit) or 0
            start_balance = 0.0
            if self.date_from:
                sql_query = "SELECT account_id, sum(debit - credit) as balance from account_move_line where account_id = %s AND date < '%s' group by account_id " % (
                    account.id, self.date_from)
                self._cr.execute(sql_query)
                start_balance = sum(r[1] for r in self._cr.fetchall())
            current_dict['accounts'].append({
                'account': account,
                'debit': debit,
                'credit': credit,
                'balance': balance + start_balance,
                'start_balance': start_balance,
            })
            current_dict['debit'] += debit
            current_dict['credit'] += credit
            current_dict['balance'] += balance + start_balance
            current_dict['start_balance'] += start_balance

        for group in child_group:
            self.add_group_to_data(group, current_dict['child_groups'], _where)

        for child_group in current_dict['child_groups'].keys():
            child_dict = current_dict['child_groups'][child_group]
            current_dict['debit'] += child_dict['debit']
            current_dict['credit'] += child_dict['credit']
            current_dict['balance'] += child_dict['balance']
            current_dict['start_balance'] += child_dict['start_balance']

    def get_report_data(self):
        group_data = {}
        _where = ''
        if self.date_from:
            _where = " AND date >= '%s'" %(self.date_from)
        if self.date_to:
            _where = " AND date <= '%s'" % (self.date_to)
        groups = self.env['account.group'].search([('id', 'child_of', self.account_group_ids.ids)])
        parent_groups = groups.filtered(lambda g: not g.parent_id or g.parent_id.id not in groups.ids)
        for p_group in parent_groups:
            self.add_group_to_data(p_group,group_data,_where)

        return group_data
    
    def add_excel_sheet(self,workbook,group_data,sheet_name):
        worksheet = workbook.add_sheet(sheet_name)

        lang = self.env.user.lang
        if lang == "ar_SY":
            worksheet.cols_right_to_left = 1

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

        # TABLE_data_tolal_line.num_format_str = '#,##0.00'
        TABLE_data_o = xlwt.easyxf(
            'font: bold 1, name Aharoni, color-index black,height 150;'
            'align: vertical center, horizontal center, wrap off;'
            'borders: left thin, right thin, top thin, bottom thin;'
            'pattern: pattern solid, pattern_fore_colour gray11, pattern_back_colour gray11'
        )
        STYLE_LINE_Data = STYLE_LINE
        STYLE_LINE_Data.num_format_str = '#,##0.00_);(#,##0.00)'

        worksheet.panes_frozen = True
        worksheet.set_horz_split_pos(4)

        row = 0
        worksheet.write_merge(row, row, 0, 1, _('تقرير ارصدة الحسابات الرئيسية'), header_format)
        row += 1
        worksheet.write_merge(row, row , 0, 0,_('التاريخ من'), TABLE_data)
        worksheet.write_merge(row, row , 1, 1,self.date_from or '', TABLE_data)
        worksheet.write_merge(row, row , 2, 2,_('التاريخ الى'), TABLE_data)
        worksheet.write_merge(row, row , 3, 3,self.date_to or '', TABLE_data)

        row += 2
        worksheet.write(row, 0, _('نوع الحساب'), header_format)
        worksheet.write(row, 1, _('اسم الحساب'), header_format)
        worksheet.write(row, 2, _('كود الحساب'), header_format)
        worksheet.write(row, 3, _('رصيد افتتاحي'), header_format)
        worksheet.write(row, 4, _('اجمالي مدين'), header_format)
        worksheet.write(row, 5, _('اجمالي دائن'), header_format)
        worksheet.write(row, 6, _('الرصيد'), header_format)
        for group in group_data.keys():
            row = self.display_group_data(worksheet, group, group_data, header_format,
                                    TABLE_data, row)

    def display_group_data(self,worksheet,group,group_data_dict,header_format,TABLE_data,row):
        dict_data = group_data_dict[group]
        row += 1
        col = 0
        worksheet.write(row , col, _('حساب رئيسي'), header_format)
        col += 1
        worksheet.write(row , col, group.name, header_format)
        col += 1
        worksheet.write(row , col, group.code_prefix, header_format)
        col += 1
        worksheet.write(row , col, dict_data['start_balance'], header_format)
        col += 1
        worksheet.write(row , col, dict_data['debit'], header_format)
        col += 1
        worksheet.write(row , col, dict_data['credit'], header_format)
        col += 1
        worksheet.write(row , col, dict_data['balance'], header_format)
        for account_data in dict_data['accounts']:
            row += 1
            col = 0
            worksheet.write(row, col, _('حساب فرعي'), TABLE_data)
            col += 1
            worksheet.write(row, col, account_data['account'].name, TABLE_data)
            col += 1
            worksheet.write(row, col, account_data['account'].code, TABLE_data)
            col += 1
            worksheet.write(row, col, account_data['start_balance'], TABLE_data)
            col += 1
            worksheet.write(row, col, account_data['debit'], TABLE_data)
            col += 1
            worksheet.write(row, col, account_data['credit'], TABLE_data)
            col += 1
            worksheet.write(row, col, account_data['balance'], TABLE_data)

        for child_group in dict_data['child_groups']:
            row = self.display_group_data(worksheet, child_group, dict_data['child_groups'], header_format, TABLE_data, row)

        return row


    def action_print_report(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('Date from can not be after date to'))
        
        self.ensure_one()
        workbook = xlwt.Workbook()


        group_data = self.get_report_data()
        self.add_excel_sheet(workbook,group_data,_('تقرير ارصدة الحسابات الرئيسية'))

        xls_file_path = (_('تقرير ارصدة الحسابات الرئيسية.xls'))

        output = BytesIO()

        workbook.save(output)

        attachment_model = self.env['ir.attachment']
        attachment_model.search([('res_model', '=', 'account.grouped.report'), ('res_id', '=', self.id)]).unlink()
        attachment_obj = attachment_model.create({
            'name': xls_file_path,
            'res_model': 'account.grouped.report',
            'res_id': self.id,
            'type': 'binary',
            'db_datas': base64.b64encode(output.getvalue()),
        })

        # Close the String Stream after saving it in the attachments
        output.close()
        url = '/web/content/%s/%s' % (attachment_obj.id,   xls_file_path)
        return {'type': 'ir.actions.act_url', 'url': url, 'target': 'new'}
            


        


