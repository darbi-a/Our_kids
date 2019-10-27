# -*- coding: utf-8 -*-
import time
import re
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class Reportquittance_report(models.AbstractModel):

    _name = 'report.product_history.report_product_history_view'


    def _get_report_data(self, ids):
        data = []
        obj_inst = self.env["product.template"]
        rec=obj_inst.browse(ids)

        indx=1
        for r in rec:

            res = {
                "id": indx,
                "name": r.name,
                "create_uid": r.create_uid,
                "create_date": r.create_date,
                "last_update": r.activity,

            }
            indx +=1
            data.append(res)
        if data:
            return data
        else:
            return {}


    @api.model
    def _get_report_values(self, docids, data=None):
        print('docids == >> ',docids)


        report_data = self._get_report_data(docids)

        return {
            'docs': report_data,
        }
