# -*- coding: utf-8 -*-
""" init object """
import barcode
import treepoem
from barcode.writer import ImageWriter
import tempfile
import base64
from io import BytesIO
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


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # barcode_image = fields.Binary(compute='compute_barcode_image',store=True)

    # @api.depends('barcode')
    def get_barcode_image(self):
        for rec in self:
            if rec.barcode:
                CODE = barcode.get_barcode_class('code128')
                result_barcode = CODE(rec.barcode,writer=ImageWriter())
                file_path = tempfile.gettempdir() + '/' + rec.barcode + '.png'
                # file_path = tempfile.gettempdir() + '\\' + rec.barcode + '.png'
                f = open(file_path,'wb')
                result_barcode.write(f)
                f.close()
                # output = BytesIO()
                f = open(file_path, 'rb')
                barcode_image = base64.b64encode(f.read())
                f.close()
                return barcode_image

    def get_barcode_tree_image(self):
        for rec in self:
            if rec.barcode:
                image = treepoem.generate_barcode(barcode_type='code128', data=rec.barcode)
                # barcode_image = base64.b64encode(image.tobytes())
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                barcode_image = base64.b64encode(buffered.getvalue())

                # test
                # file_path = tempfile.gettempdir() + '/' + rec.barcode + '.png'
                # f = open(file_path,'wb')
                # image.save(f)
                # f.close()
                # end of test

                return barcode_image

    def get_product_print_data(self):
        return{
            'display_name': self.display_name,
            'price': self.lst_price,
            'barcode_image': self.get_barcode_tree_image(),
            # 'barcode_image': self.get_barcode_image(),
            'currency_id': self.company_id.currency_id,
            'barcode': self.barcode,
            'vendor_color': self.vendor_color,
        }


