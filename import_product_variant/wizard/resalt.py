#-*- coding: utf-8 -*-

import base64
import csv
import os
import tempfile

import xlrd
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class resaltProductVariant(models.TransientModel):
    _name = "wizard.resalt.variant"

    count_items = fields.Integer('Number Of Items Created', readonly=True, )
    count_items_edit = fields.Integer('Number Of Items Modified', readonly=True, )
    count_variant = fields.Integer('Number Of Variant Created', readonly=True, )
    count_edit = fields.Integer('Number Of Variant Modified', readonly=True, )

