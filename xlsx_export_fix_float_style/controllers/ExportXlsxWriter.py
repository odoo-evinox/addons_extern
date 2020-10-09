# Copyright 2020 NextERP Romania SRL
import datetime
import odoo
from odoo import http
from odoo.http import request
#from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
from odoo.addons.web.controllers.main import ExportXlsxWriter
from odoo.addons.web.controllers.main import GroupExportXlsxWriter
from odoo.addons.web.controllers.main import ExcelExport
from odoo.addons.web.controllers.main import serialize_exception

from odoo.tools import image_process, topological_sort, html_escape, pycompat, ustr, apply_inheritance_specs, lazy_property
from odoo.exceptions import AccessError, UserError, AccessDenied

# with replace the instance functions ( just defined the functions without class and no class ExcelExport)
# ExportXlsxWriter.get_cell_style = get_cell_style
# ExportXlsxWriter.write_cell = write_cell
# GroupExportXlsxWriter._write_group_header = _write_group_header


# with inheritance
class ExcelExport2(ExcelExport):
 
    @http.route('/web/export/xlsx', type='http', auth="user")
    @serialize_exception
    def index(self, data, token):
        return self.base(data, token)

    def from_group_data(self, fields, groups):
        with GroupExportXlsxWriter2(fields, groups.count) as xlsx_writer:
            x, y = 1, 0
            for group_name, group in groups.children.items():
                x, y = xlsx_writer.write_group(x, y, group_name, group)
 
        return xlsx_writer.value
 
    def from_data(self, fields, rows):
        with ExportXlsxWriter2(fields, len(rows)) as xlsx_writer:
            for row_index, row in enumerate(rows):
                for cell_index, cell_value in enumerate(row):
                    if isinstance(cell_value, (list, tuple)):
                        cell_value = pycompat.to_text(cell_value)
                    xlsx_writer.write_cell(row_index + 1, cell_index, cell_value)
 
        return xlsx_writer.value
 
 
class ExportXlsxWriter2(ExportXlsxWriter):
    def write_cell(self, row, column, cell_value):
        cell_style = self.get_cell_style(column, cell_value)
        self.write(row, column, cell_value, cell_style)
         
    def get_cell_style(self, column, cell_value, header_style=False, header_bold_style=False):
        "returns excel type of cell style( number, datetime, text ..)"
        if isinstance(cell_value, bytes):
            try:
                # because xlsx uses raw export, we can get a bytes object
                # here. xlsxwriter does not support bytes values in Python 3 ->
                # assume this is base64 and decode to a string, if this
                # fails note that you can't export
                cell_value = pycompat.to_text(cell_value)
            except UnicodeDecodeError:
                raise UserError(_("Binary fields can not be exported to Excel unless their content is base64-encoded. That does not seem to be the case for %s.") % self.field_names[column])
        if isinstance(cell_value, str):
            if len(cell_value) > self.worksheet.xls_strmax:
                cell_value = _("The content of this cell is too long for an XLSX file (more than %s characters). Please use the CSV format for this export.") % self.worksheet.xls_strmax
            else:
                cell_value = cell_value.replace("\r", " ")
 
        format = {}
        if type(cell_value) is  int:
            format = { 'num_format': '0'}
        elif isinstance(cell_value, float):
            # all floats with just 2 decimals
            format = { 'num_format': '0.00'} # asked by client
# with same number of decimals as original but max 3 # this is more general do not delete  
#             if '.' in str(cell_value):
#                 decimal_paces = len(str(cell_value).split('.')[1])
#             else:
#                 decimal_paces = 1
#             format = { 'num_format': '0.'+'0' * min(decimal_paces,3)}
        elif isinstance(cell_value, datetime.datetime):
            format = {'text_wrap': True, 'num_format': 'yyyy-mm-dd hh:mm:ss'}
        elif isinstance(cell_value, datetime.date):
            format = {'text_wrap': True, 'num_format': 'yyyy-mm-dd'}
        else: #text/string
            format = {'text_wrap': True,}
             
        if header_style:
            format.update({'bold': True, })
        if header_bold_style:
            format.update({'text_wrap': True, 'bold': True, 'bg_color': '#e9ecef'})
 
        cell_style = self.workbook.add_format(format)
        return cell_style
 
class GroupExportXlsxWriter2(GroupExportXlsxWriter, ExportXlsxWriter2):
    def _write_group_header(self, row, column, label, group, group_depth=0):
        aggregates = group.aggregated_values
 
        label = '%s%s (%s)' % ('    ' * group_depth, label, group.count)
        cell_style = self.get_cell_style(column, label, header_bold_style=True)
        self.write(row, column, label, cell_style)
        for field in self.fields[1:]: # No aggregates allowed in the first column because of the group title
            column += 1
            aggregated_value = aggregates.get(field['name'])
  
            cell_style = self.get_cell_style(column, aggregated_value,header_bold_style=True)
                 
            self.write(row, column, aggregated_value if aggregated_value is not None else '', cell_style)
        return row + 1, 0

