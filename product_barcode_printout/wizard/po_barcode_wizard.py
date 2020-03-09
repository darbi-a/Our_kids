# -*- coding: utf-8 -*-
""" init object """
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


class PoBarcodeWizard(models.TransientModel):
    _name = 'po.barcode.wizard'
    _description = 'po.barcode.wizard'

    line_ids = fields.One2many(comodel_name="po.barcode.line.wizard", inverse_name="wizard_id", string="", required=False, )


class PoBarcodeWizardLine(models.TransientModel):
    _name = 'po.barcode.line.wizard'
    _description = 'po.barcode.line.wizard'

    file_name = fields.Char()
    binary_field = fields.Binary(string="File")
    wizard_id = fields.Many2one(comodel_name="po.barcode.wizard" )
