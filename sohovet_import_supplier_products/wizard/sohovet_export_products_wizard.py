# -*- encoding: utf-8 -*-
##############################################################################
#                                                                            #
#  OpenERP, Open Source Management Solution.                                 #
#                                                                            #
#  @author Juan Ignacio Alonso Barba <jialonso@grupovermon.com>              #
#                                                                            #
#  This program is free software: you can redistribute it and/or modify      #
#  it under the terms of the GNU Affero General Public License as            #
#  published by the Free Software Foundation, either version 3 of the        #
#  License, or (at your option) any later version.                           #
#                                                                            #
#  This program is distributed in the hope that it will be useful,           #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              #
#  GNU Affero General Public License for more details.                       #
#                                                                            #
#  You should have received a copy of the GNU Affero General Public License  #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.      #
#                                                                            #
##############################################################################

from openerp import fields, models, api
from openerp.exceptions import ValidationError
import base64
import xlsxwriter
import StringIO

class sohovetExportProductsWizard(models.TransientModel):
    _name = 'sohovet.export.products.wizard'
    _description = 'Exportar productos'

    @api.multi
    def _get_data(self):
        output = StringIO.StringIO()

        workbook = xlsxwriter.Workbook(output)
        self._generateBaseWorkbook(workbook)
        self._addData(workbook)
        workbook.close()

        bin_file = base64.encodestring(output.getvalue())
        return bin_file


    @api.multi
    def _get_name(self):
        if self.env.context['active_model'] == 'res.partner':
            return 'export_%s.xlsx' % self.env['res.partner'].browse(self.env.context['active_id']).name.\
                replace(' ', '_')
        elif self.env.context['active_model'] == 'product.template':
            template_ids = self.env['product.template'].browse(self.env.context['active_ids'])
            for template_id in template_ids:
                if not template_id.seller_ids:
                    raise ValidationError('Se han seleccionado productos sin proveedor')

            supinfo_ids = self.env['product.supplierinfo'].search([('product_tmpl_id', 'in',
                                                                    self.env.context['active_ids'])])
            if supinfo_ids:
                supplier = supinfo_ids[0].name
            for supinfo in supinfo_ids[1:]:
                if supplier.id != supinfo.name.id:
                    raise ValidationError('Se han seleccionado productos de distintos proveedores')
            return 'export_%s.xlsx' % supplier.name.replace(' ', '_')

    data = fields.Binary(string='File', default=_get_data)
    name = fields.Char(string='File name', default=_get_name)

    def _generateBaseWorkbook(self, workbook):
        worksheet1 = workbook.add_worksheet('Datos')
        worksheet2 = workbook.add_worksheet('Validacion')

        text_format = workbook.add_format({'num_format': 49})
        int_format = workbook.add_format({'num_format': 1})

        text_format_req = workbook.add_format({'num_format': 49, 'bg_color': '#F5F5CE'})
        int_format_req = workbook.add_format({'num_format': 1, 'bg_color': '#F5F5CE'})
        float_format_req = workbook.add_format({'num_format': 2, 'bg_color': '#F5F5CE'})

        format_header = workbook.add_format({'bold': True, 'bg_color': '#FACC2E'})

        # VENDIBLE
        worksheet1.write('A1', 'vendible', format_header)
        worksheet1.set_column('A:A', 12, int_format_req)
        worksheet1.data_validation('A2:A1048576', {'validate': 'list', 'source': ['0', '1']})

        # REF INTERNA
        worksheet1.write('B1', 'ref_interna', format_header)
        worksheet1.set_column('B:B', 16, text_format)

        # COD PRODUCTO
        worksheet1.write('C1', 'ref_proveedor', format_header)
        worksheet1.set_column('C:C', 16, text_format)

        # EAN13
        worksheet1.write('D1', 'ean13', format_header)
        worksheet1.set_column('D:D', 16, text_format)

        # DESCRIPCION
        worksheet1.write('E1', 'descripcion', format_header)
        worksheet1.set_column('E:E', 32, text_format_req)

        # CATEGORIA
        worksheet2.write(0, 0, 'categorias', format_header)
        categ_ids = self.env['product.category'].search([('parent_id', '!=', False)])
        categ_ids = categ_ids.sorted(key=lambda r: r.name)
        for i in range(len(categ_ids)):
            worksheet2.write((i+1), 0, categ_ids[i].name)
        worksheet2.set_column('A:A', 50)

        worksheet1.write('F1', 'categoria', format_header)
        worksheet1.set_column('F:F', 24, text_format_req)
        worksheet1.data_validation('F2:F1048576', {'validate': 'list', 'source': '=Validacion!$A$2:$A$%d' % (i+2)})

        # GRUPO
        worksheet2.write(0, 1, 'grupos', format_header)
        group_ids = self.env['sohovet.product.group'].search([])
        group_ids = group_ids.sorted(key=lambda r: r.name)
        for i in range(len(group_ids)):
            worksheet2.write((i+1), 1, group_ids[i].name)
        worksheet2.set_column('B:B', 24)

        worksheet1.write('G1', 'grupo', format_header)
        worksheet1.set_column('G:G', 24, text_format_req)
        worksheet1.data_validation('G2:G1048576', {'validate': 'list', 'source': '=Validacion!$B$2:$B$%d' % (i+2)})

        # MARCAS
        worksheet2.write(0, 2, 'marcas', format_header)
        brand_ids = self.env['sohovet.product.brand'].search([])
        brand_ids = brand_ids.sorted(key=lambda r: r.name)
        for i in range(len(brand_ids)):
            worksheet2.write((i+1), 2, brand_ids[i].name)
        worksheet2.write((i+1), 2, '*')  # MARCA *
        worksheet2.set_column('C:C', 24)

        worksheet1.write('H1', 'marca', format_header)
        worksheet1.set_column('H:H', 24, text_format)
        worksheet1.data_validation('H2:H1048576', {'validate': 'list', 'source': '=Validacion!$C$2:$C$%d' % (i+3)})

        # UNIDADES COMPRA
        worksheet1.write('I1', 'unidades_compra', format_header)
        worksheet1.set_column('I:I', 16, int_format_req)
        worksheet1.data_validation('I2:I1048576', {'validate': 'integer', 'criteria': '>', 'value': 0})

        # UNIDAD DE COMPRA
        worksheet2.write(0, 3, 'unidad_compra', format_header)
        uom_ids = self.env['product.uom'].search([('uom_type', '=', 'reference')])
        for i in range(len(uom_ids)):
            worksheet2.write((i+1), 3, uom_ids[i].name)
        worksheet2.set_column('D:D', 16)

        worksheet1.write('J1', 'unidad_compra', format_header)
        worksheet1.set_column('J:J', 16, text_format_req)
        worksheet1.data_validation('J2:J1048576', {'validate': 'list', 'source': '=Validacion!$D$2:$D$%d' % (i+2)})

        # COSTE COMPRA
        worksheet1.write('K1', 'coste_compra', format_header)
        worksheet1.set_column('K:K', 16, float_format_req)
        worksheet1.data_validation('K2:K1048576', {'validate': 'decimal', 'criteria': '>', 'value': 0})

        # IVA_COMPRA
        worksheet2.write(0, 4, 'iva_compra', format_header)
        ivas_compra = [4, 10, 21]
        for i in range(len(ivas_compra)):
            worksheet2.write((i+1), 4, ivas_compra[i])
        worksheet2.set_column('E:E', 16)

        worksheet1.write('L1', 'iva_compra', format_header)
        worksheet1.set_column('L:L', 16, int_format_req)
        worksheet1.data_validation('L2:L1048576', {'validate': 'list', 'source': '=Validacion!$E$2:$E$%d' % (i+2)})

        # IVA_VENTA
        worksheet2.write(0, 5, 'iva_venta', format_header)
        ivas_venta = [4, 10, 21]
        for i in range(len(ivas_venta)):
            worksheet2.write((i+1), 5, ivas_venta[i])
        worksheet2.set_column('F:F', 16)

        worksheet1.write('M1', 'iva_venta', format_header)
        worksheet1.set_column('M:M', 16, int_format_req)
        worksheet1.data_validation('M2:M1048576', {'validate': 'list', 'source': '=Validacion!$F$2:$F$%d' % (i+2)})

        # DESCUENTO
        worksheet1.write('N1', 'descuento', format_header)
        worksheet1.set_column('N:N', 16, text_format)

        # STOCK_MIN
        worksheet1.write('O1', 'stock_min', format_header)
        worksheet1.set_column('O:O', 16, int_format)
        worksheet1.data_validation('O2:O1048576', {'validate': 'integer', 'criteria': '>=', 'value': 0})

        # UBICACIONES
        worksheet2.write(0, 6, 'ubicaciones', format_header)
        warehouse_ids = self.env['stock.warehouse'].search([])
        warehouse_ids = warehouse_ids.sorted(key=lambda r: r.name)
        for i in range(len(warehouse_ids)):
            worksheet2.write((i+1), 6, warehouse_ids[i].code)
        worksheet2.set_column('G:G', 16)

        worksheet1.write('P1', 'ubicacion', format_header)
        worksheet1.set_column('P:P', 16, text_format)
        worksheet1.data_validation('P2:P1048576', {'validate': 'list', 'source': '=Validacion!$G$2:$G$%d' % (i+2)})

        worksheet2.protect()

    def _addData(self, workbook):
        if self.env.context['active_model'] == 'res.partner':
            supinfo_ids = self.env['product.supplierinfo'].search([('name', '=', self.env.context['active_id'])])
        elif self.env.context['active_model'] == 'product.template':
            supinfo_ids = self.env['product.supplierinfo'].search([('product_tmpl_id', 'in', self.env.context['active_ids'])])

        worksheet = workbook.worksheets_objs[0]
        i = 1
        for supinfo_id in supinfo_ids:
            template_id = supinfo_id.product_tmpl_id
            if not (template_id.active and template_id.purchase_ok):
                continue

            stock_rules = self.env['stock.warehouse.orderpoint'].search([('product_id', 'in',
                                                                    [p.id for p in template_id.product_variant_ids])])
            qtys = []
            codes = []
            for rule in stock_rules:
                qtys.append(str(int(rule.product_min_qty)))
                codes.append(rule.warehouse_id.code)

            fields = [
                1 if template_id.sale_ok else 0,
                template_id.default_code,
                supinfo_id.product_code,
                template_id.ean13,
                supinfo_id.product_name if supinfo_id.product_name else template_id.name,
                template_id.categ_id.name,
                template_id.group_id.name,
                template_id.brand_id.name,
                int(template_id.purchase_uom_factor),
                template_id.uom_id.name if template_id.uom_id else None,
                template_id.purchase_uom_price,
                int(template_id.supplier_taxes_id[0].amount * 100) if template_id.supplier_taxes_id else None,
                int(template_id.taxes_id[0].amount * 100) if template_id.taxes_id else None,
                supinfo_id.supplier_discount,
                '/'.join(qtys),
                '/'.join(codes),
            ]

            for j in range(len(fields)):
                if fields[j]:
                    worksheet.write(i, j, fields[j], worksheet.col_formats[j])

            i += 1
