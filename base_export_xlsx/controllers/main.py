
import datetime
import io
import logging
import re
import xlsxwriter

from odoo.tools import pycompat
from odoo.tools.translate import _
from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo.addons.web.controllers.main import ExcelExport

_logger = logging.getLogger(__name__)


class ExcelExportInherit(ExcelExport):

    def filename(self, base):
        return base + '.xlsx'

    def from_data(self, fields, rows):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sheet 1')
        worksheet.freeze_panes(1, 0)

        date_default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
        default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'})
        title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2})

        for i, fieldname in enumerate(fields):
            worksheet.write(0, i, fieldname, title_style)
            worksheet.set_column(i, i, 25) # around 220 pixels

        for row_index, row in enumerate(rows):
            for cell_index, cell_value in enumerate(row):
                cell_style = default_style

                if isinstance(cell_value, bytes) and not isinstance(cell_value, pycompat.string_types):
                    try:
                        cell_value = pycompat.to_text(cell_value)
                    except UnicodeDecodeError:
                        raise UserError(_("Binary fields can not be exported to Excel unless their content is base64-encoded. That does not seem to be the case for %s.") % fields[cell_index])

                if isinstance(cell_value, pycompat.string_types):
                    cell_value = re.sub("\r", " ", pycompat.to_text(cell_value))
                    cell_value = cell_value[:32767]
                elif isinstance(cell_value, datetime.datetime):
                    cell_style = date_default_style
                elif isinstance(cell_value, datetime.date):
                    cell_style = date_default_style
                worksheet.write(row_index + 1, cell_index, cell_value, cell_style)

        workbook.close()
        output.seek(0)
        data = output.read()
        output.close()
        return data
