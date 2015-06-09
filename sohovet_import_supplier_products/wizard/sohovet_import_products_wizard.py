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
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
import openerp.addons.decimal_precision as dp
import openerp.addons.product.product
import StringIO

import base64

valid_fields = [
    'ref_interna', 'ref_proveedor', 'ean13', 'descripcion', 'categoria', 'grupo', 'marca', 'unidades_compra',
    'unidad_compra', 'coste_compra', 'iva_compra', 'iva_venta', 'descuento', 'vendible', 'stock_min', 'ubicacion',
]

SALE_TAX_TEMPLATE = 'S_IVA%s'
PURCHASE_TAX_TEMPLATE = 'P_IVA%s_BC'

def xlsx(bin_file):
    import zipfile
    from xml.etree.ElementTree import iterparse
    z = zipfile.ZipFile(bin_file)
    strings = [el.text for e, el in iterparse(z.open('xl/sharedStrings.xml')) if el.tag.endswith('}t')]
    header = {}
    rows = []
    row = {}
    value = ''
    for e, el in iterparse(z.open('xl/worksheets/sheet1.xml')):
        if el.tag.endswith('}v'): # <v>84</v>
            value = el.text
        if el.tag.endswith('}c'): # <c r="A3" t="s"><v>84</v></c>
            if el.attrib.get('t') == 's':
                value = strings[int(value)]
            letter = el.attrib['r'] # AZ22
            while letter[-1].isdigit():
                letter = letter[:-1]
            if header:
                row[header[letter]] = value
            else:
                row[letter] = value
            value = ''
        if el.tag.endswith('}row'):
            if header and row:
                rows.append(row)
            else:
                header = row
            row = {}
    return header.values(), rows

class sohovet_import_products_wizard(models.TransientModel):
    _name = 'sohovet.import.products.wizard'
    _description = 'Importar productos por proveedor'

    def _get_supplier_id(self):
        return self.env['res.partner'].search([('id', '=', self.env.context['active_id'])])

    supplier_id = fields.Many2one('res.partner', 'Proveedor', default=_get_supplier_id, required=True, readonly=True)
    xlsx_file = fields.Binary(string='Fichero XLSX', required=True)

    @api.multi
    def read_csv(self):
        try:
            bin_file = StringIO.StringIO(base64.b64decode(self.xlsx_file))
            header, rows = xlsx(bin_file)

            # PROCESS ROWS
            items = []
            for row in rows:
                print row
                item = self._read_fields(row)
                items.append(item)

        except Exception as e:
            raise ValidationError(_('No se pudo leer el fichero XLSX:\n%s' % e))

        try:
            import_data = {
                'supplier_id': self.supplier_id.id,
            }
            import_products = self.env['sohovet.import.products'].create(import_data)
            import_items = []
            for item in items:
                item['import_id'] = import_products.id
                import_item = self.env['sohovet.import.products.item'].create(item)
                import_items.append(import_item.id)
            import_products.item_ids = [(6, 0, import_items)]
        except Exception as e:
            raise ValidationError(_('Formato incorrecto en el fichero XLSX:\n%s' % e))

        return {'name': 'Importar productos',
                'res_id': import_products.id,
                'res_model': 'sohovet.import.products',
                'target': 'current',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                # 'view_id': self.env.ref('sohovet_import_supplier_products.sohovet_add_products_wizard').id,
        }


    def _read_fields(self, fields):
        vals = {}
        if 'ref_interna' in fields and fields['ref_interna']:
            vals['ref_interna'] = fields['ref_interna']

        if 'ref_proveedor' in fields and fields['ref_proveedor']:
            vals['ref_proveedor'] = fields['ref_proveedor']

        if 'descripcion' in fields and fields['descripcion']:
            vals['descripcion'] = fields['descripcion']

        if 'descuento' in fields and fields['descuento']:
            vals['descuento'] = fields['descuento']

        if 'categoria' in fields and fields['categoria']:
            category_id = self.env['product.category'].search([('name', 'ilike', fields['categoria']),
                                                               ('type', '=', 'normal')])
            if category_id:
                vals['categoria'] = category_id.id

        if 'grupo' in fields and fields['grupo']:
            group_id = self.env['sohovet.product.group'].search([('name', 'ilike', fields['grupo'])])
            if group_id:
                vals['grupo'] = group_id.id

        if 'marca' in fields and fields['marca']:
            if fields['marca'] == '*':
                vals['marca'] = self.env.ref('sohovet_import_supplier_products.remove_brand').id
            else:
                brand_id = self.env['sohovet.product.brand'].search([('name', 'ilike', fields['marca'])])
                if brand_id:
                    vals['marca'] = brand_id.id

        if 'unidades_compra' in fields and fields['unidades_compra']:
            vals['unidades_compra'] = int(fields['unidades_compra'])

        if 'unidad_compra' in fields and fields['unidad_compra']:
            uom_id = self.env['product.uom'].search([('name', 'ilike', fields['unidad_compra'])])
            if uom_id:
                vals['product_uom'] = uom_id.id

        if 'coste_compra' in fields and fields['coste_compra']:
            vals['coste_compra'] = float(fields['coste_compra'].replace(',', '.'))

        if 'ean13' in fields and fields['ean13']:
            if fields['ean13'] == '*' or openerp.addons.product.product.check_ean(fields['ean13']):
                vals['ean13'] = fields['ean13']

        if 'iva_compra' in fields and fields['iva_compra']:
            tax_id = self.env['account.tax'].search([('name', '=', PURCHASE_TAX_TEMPLATE % fields['iva_compra'])])
            if tax_id:
                vals['iva_compra'] = tax_id.id

        if 'iva_venta' in fields and fields['iva_venta']:
            tax_id = self.env['account.tax'].search([('name', '=', SALE_TAX_TEMPLATE % fields['iva_venta'])])
            if tax_id:
                vals['iva_venta'] = tax_id.id

        if 'vendible' in fields and fields['vendible']:
            vals['vendible'] = fields['vendible'] != '0'

        if 'stock_min' in fields and 'ubicacion' in fields and fields['stock_min'] and fields['ubicacion']:
            if fields['stock_min'].isdigit() and not '/' in fields['ubicacion']:  # Varias ubicaciones...
                warehouse_id = self.env['stock.warehouse'].search([('code', '=', fields['ubicacion'])])
                if warehouse_id:
                    vals['stock_min'] = int(fields['stock_min'])
                    vals['ubicacion'] = warehouse_id.id

        return vals