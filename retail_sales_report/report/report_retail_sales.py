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


class RetailSalesReport(models.AbstractModel):
    _name = 'report.retail_sales_report.report_retail_sales'
    _description = 'Retail Sales Report'


    @api.multi
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        data['docs'] = self.env['retail.sales.report.wizard'].browse(docids)
        return data