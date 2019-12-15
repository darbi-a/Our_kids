# -*- coding: utf-8 -*-
""" init object """
import barcode
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

    barcode_image = fields.Binary(compute='compute_barcode_image')

    @api.depends('barcode')
    def compute_barcode_image(self):
        for rec in self:
            if rec.barcode:
                CODE = barcode.get_barcode_class('code128')
                result_barcode = CODE(rec.barcode,writer=ImageWriter())
                file_path = tempfile.gettempdir() + '/' + rec.barcode + '.png'
                f = open(file_path,'wb')
                result_barcode.write(f)
                f.close()
                # output = BytesIO()
                f = open(file_path, 'rb')
                rec.barcode_image = base64.b64encode(f.read())
                f.close()


