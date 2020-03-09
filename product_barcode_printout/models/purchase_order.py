# -*- coding: utf-8 -*-
""" init object """
import base64
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


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def get_barcode_files_wizard(self,template):
        barcode_wiz = self.env['po.barcode.wizard'].create({})
        labels_per_file = 1000
        labels_count = 0
        order_lines = self.env['purchase.order.line']
        i = 0
        lines_count = len(self.order_line)
        f_count = 0
        for line in self.order_line:
            labels_count += int(line.product_qty)
            order_lines |= line
            if labels_count > labels_per_file or i == lines_count-1:
                data = {'order_lines': order_lines}
                pdf = self.env.ref(template).render_qweb_pdf(self.ids, data=data)[0]
                pdf = base64.b64encode(pdf)
                f_count += 1
                file_name = 'Labels of ' + self.name + ' - ' + str(f_count)
                wiz_line = self.env['po.barcode.line.wizard'].create({'wizard_id': barcode_wiz.id,'binary_field':pdf,'file_name':file_name})
                order_lines = self.env['purchase.order.line']
                labels_count = 0
            i += 1

        view_form = {
            'name': _('Purchase Barcode '),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'po.barcode.wizard',
            'type': 'ir.actions.act_window',
            'res_id': barcode_wiz.id,
            'target': 'new',

        }

        return view_form

    def print_large_label(self):
        view_form = self.get_barcode_files_wizard('product_barcode_printout.purchase_order_product_label_report')
        return view_form

    def print_small_label(self):
        view_form = self.get_barcode_files_wizard('product_barcode_printout.purchase_order_product_label_report_2')
        return view_form


