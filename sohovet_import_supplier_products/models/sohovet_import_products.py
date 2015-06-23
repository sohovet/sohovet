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

import base64
import re

SALE_TAX_PATTERN = '^S_IVA[0-9]+$'
PURCHASE_TAX_PATTERN = '^P_IVA[0-9]+_BC$'

class sohovet_import_products(models.Model):
    _name = 'sohovet.import.products'
    _rec_name = 'supplier_id'
    _order = 'create_date desc'

    supplier_id = fields.Many2one('res.partner', 'Proveedor', required=True, readonly=True)
    description_mode = fields.Selection(selection=[('both', 'En las fichas del producto y del proveedor'),
                                                   ('product', 'Sólo en la ficha de producto'),
                                                   ('supplier', 'Sólo en la ficha del proveedor')],
                                      string='Actualizar descripción', default='supplier', required=True)
    item_ids = fields.One2many('sohovet.import.products.item', 'import_id')
    item_ids2 = fields.One2many('sohovet.import.products.item', 'import_id', related='item_ids')
    item_ids3 = fields.One2many('sohovet.import.products.item', 'import_id', related='item_ids')
    state = fields.Selection([('confirm_data', 'Confirmar datos'), ('confirm_price', 'Revisar precios'),
                              ('imported', 'Importado'), ('cancelled', 'Cancelado')], default='confirm_data')

    @api.multi
    def save_items(self):
        self.state = 'confirm_price'

    @api.multi
    def save_prices(self):
        for item in self.item_ids:
            item.save_item()
        self.state = 'imported'
        other_imports_ids = self.search([('supplier_id', '=', self.supplier_id.id), ('state', '!=', 'imported')])
        for import_id in other_imports_ids:
            import_id.state = 'cancelled'


    @api.multi
    def back_to_confirm_data(self):
        self.state = 'confirm_data'

    @api.multi
    def open_product_cost(self):
        action = {
            'name': 'Cost prices',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree',
            'view_type': 'form',
            'context': '{"search_default_filter_to_purchase": 1}',
            'view_id': self.env.ref('sohovet_product_price.set_cost_tree_view').id,
            'search_view_id': self.env.ref('sohovet_product_price.sohovet_set_cost_search_view').id,
            'domain': [("id", "in", [item.template_id.id for item in self.item_ids])]
        }
        return action

    @api.multi
    def open_product_prices(self):
        action = {
            'name': 'Sell prices',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree',
            'view_type': 'form',
            'view_id': self.env.ref('sohovet_product_price.set_pvp_tree_view').id,
            'search_view_id': self.env.ref('sohovet_product_price.sohovet_set_pvp_search_view').id,
            'domain': [("id", "in", [item.template_id.id for item in self.item_ids])]
        }
        return action

class sohovet_import_products_items(models.Model):
    _name = 'sohovet.import.products.item'
    _rec_name = 'template_id'

    state = fields.Selection(related='import_id.state')
    import_user = fields.Many2one('res.users', related='import_id.write_uid')
    import_date = fields.Datetime(related='import_id.write_date')

    import_id = fields.Many2one('sohovet.import.products', 'Import ID', ondelete='cascade')
    supplier_id = fields.Many2one('res.partner', 'Proveedor', related='import_id.supplier_id', required=True)
    template_id = fields.Many2one('product.template', 'Producto', compute='_get_product', store=True)
    new_product = fields.Boolean('Nuevo', compute='_get_product', store=True)
    ref_interna = fields.Char('Referencia interna', readonly=True)
    ref_proveedor = fields.Char('Referencia proveedor')
    ean13 = fields.Char('EAN13')
    descripcion = fields.Char('Descripción')
    product_uom = fields.Many2one('product.uom', 'Unidad', domain=[('uom_type', '=', 'reference')])
    categoria = fields.Many2one('product.category', 'Categoria')
    grupo = fields.Many2one('sohovet.product.group', 'Grupo')
    marca = fields.Many2one('sohovet.product.brand', 'Marca')
    unidades_compra = fields.Integer('Unidades de compra')
    coste_compra = fields.Float('Coste de compra', digits=dp.get_precision('Product Price'))
    iva_compra = fields.Many2one('account.tax', 'IVA compra')
    iva_compra_sel = fields.Selection(selection='_get_iva_compra_sel_items', string='IVA compra',
                                      compute='_get_iva_compra_sel', inverse='_set_iva_compra_sel')
    iva_venta = fields.Many2one('account.tax', 'IVA venta')
    iva_venta_sel = fields.Selection(selection='_get_iva_venta_sel_items', string='IVA venta',
                                     compute='_get_iva_venta_sel', inverse='_set_iva_venta_sel')
    descuento = fields.Integer('Descuento proveedor')
    vendible = fields.Boolean('Vendible')
    stock_min = fields.Integer('Stock minimo')
    ubicacion = fields.Many2one('stock.location', 'Ubicación')

    precio_coste = fields.Float('Precio coste nuevo', digits=dp.get_precision('Product Price'), compute='_get_cost_price')
    precio_coste_actual = fields.Float('Precio coste actual', digits=dp.get_precision('Product Price'),
                                         related='template_id.standard_price', readonly=True)

    margen_categoria = fields.Integer('Margen categoria nuevo (%)', related='categoria.category_margin', readonly=True)
    margen_categoria_actual = fields.Integer('Margen categoria actual (%)', related='template_id.category_margin', readonly=True)

    stock_minimo_actual = fields.Char('Stock minimo actual', compute='_get_stock_minimo_actual')
    stock_minimo_nuevo = fields.Char('Stock minimo nuevo', compute='_get_stock_minimo_nuevo')

    @api.multi
    def _get_iva_compra_sel_items(self):
        taxes = []
        for tax in self.env['account.tax'].search([]):
            if tax.amount != 0 and re.match(PURCHASE_TAX_PATTERN, tax.name):
                taxes.append((str(tax.id), tax.amount))
        taxes = sorted(taxes, key=lambda amount: amount[1])
        for i in range(len(taxes)):
            taxes[i] = (taxes[i][0], '%d%%' % (taxes[i][1] * 100))
        return taxes

    @api.one
    @api.depends('iva_compra')
    def _get_iva_compra_sel(self):
        if self.iva_compra:
            self.iva_compra_sel = str(self.iva_compra.id)

    @api.one
    def _set_iva_compra_sel(self):
        self.iva_compra = self.env['account.tax'].browse(int(self.iva_compra_sel))

    @api.multi
    def _get_iva_venta_sel_items(self):
        taxes = []
        for tax in self.env['account.tax'].search([]):
            if tax.amount != 0 and re.match(SALE_TAX_PATTERN, tax.name):
                taxes.append((str(tax.id), tax.amount))
        taxes = sorted(taxes, key=lambda amount: amount[1])
        for i in range(len(taxes)):
            taxes[i] = (taxes[i][0], '%d%%' % (taxes[i][1] * 100))
        return taxes

    @api.one
    @api.depends('iva_venta')
    def _get_iva_venta_sel(self):
        if self.iva_venta:
            self.iva_venta_sel = str(self.iva_venta.id)

    @api.one
    def _set_iva_venta_sel(self):
        self.iva_venta = self.env['account.tax'].browse(int(self.iva_venta_sel))

    @api.one
    @api.depends('supplier_id', 'ref_proveedor')
    def _get_product(self):
        self.template_id = None
        self.new_product = True

        if self.ref_interna:
            self.template_id = self.env['product.template'].search([('default_code', '=', self.ref_interna)])
            self.new_product = False
            if not self.template_id:
                raise ValidationError('Producto con referencia interna %s no encontrado' % self.ref_interna)

        if self.ref_proveedor:
            product_supinfo = self.env['product.supplierinfo'].search([('name', '=', self.supplier_id.id),
                                                                       ('product_code', '=', self.ref_proveedor)])
            if product_supinfo:
                product_supinfo = product_supinfo[0]
                self.template_id = product_supinfo.product_tmpl_id
                self.new_product = False

    @api.one
    @api.onchange('template_id')
    def _on_change_template_id(self):
        self.product_uom = self.template_id.uom_id

    @api.one
    @api.depends('coste_compra', 'unidades_compra')
    def _get_cost_price(self):
        if self.unidades_compra and self.unidades_compra != 0:
            self.precio_coste = self.coste_compra / self.unidades_compra

    @api.onchange('ean13')
    def _chek_ean(self):
        if self.ean13 and self.ean13 != '*' and not openerp.addons.product.product.check_ean(self.ean13):
            self.ean13 = ''

    @api.one
    @api.depends('template_id')
    def _get_stock_minimo_actual(self):
        if self.template_id:
            rules = self.env['stock.warehouse.orderpoint'].search([('product_id', 'in',
                                                                    [p.id for p in self.template_id.product_variant_ids])])
            aux_list = []
            for rule in rules:
                aux_str = '%s:%d' % (rule.location_id.code, rule.product_min_qty)
                aux_list.append(aux_str)
            if aux_list:
                self.stock_minimo_actual = ' / '.join(aux_list)

    @api.one
    @api.depends('template_id', 'stock_min', 'ubicacion')
    def _get_stock_minimo_nuevo(self):
        rules = self.env['stock.warehouse.orderpoint'].search([('product_id', 'in',
                                                                [p.id for p in self.template_id.product_variant_ids])])
        aux_list = []
        contains = False
        for rule in rules:
            if self.ubicacion and self.ubicacion.id == rule.location_id.id:
                contains = True
                if self.stock_min > 0:
                    aux_str = '%s:%d' % (rule.location_id.code, self.stock_min)
                    aux_list.append(aux_str)
            else:
                aux_str = '%s:%d' % (rule.location_id.code, rule.product_min_qty)
                aux_list.append(aux_str)

        if self.ubicacion and not contains and self.stock_min > 0:
                aux_str = '%s:%d' % (self.ubicacion.code, self.stock_min)
                aux_list.append(aux_str)

        if aux_list:
            self.stock_minimo_nuevo = ' / '.join(aux_list)

    @api.one
    def save_item(self):
        if self.template_id:
            self.update_template()
        else:
            self.create_template()


    @api.one
    def create_template(self):
        if not (self.descripcion and self.categoria and self.grupo and self.unidades_compra > 0
                and self.coste_compra > 0 and self.iva_compra and (not self.vendible or self.vendible and self.iva_venta)):
            raise ValidationError('Faltan datos para crear el producto %s' % self.descripcion)

        template_data = {
            'name': self.descripcion,
            'categ_id': self.categoria.id,
            'group_id': self.grupo.id,
            'uom_id': self.product_uom.id,
            'uom_po_id': self.product_uom.id,
        }
        self.template_id = self.env['product.template'].create(template_data)
        self.ref_interna = self.template_id.default_code

        supinfo_data = {
            'name': self.supplier_id.id,
            'product_tmpl_id': self.template_id.id,
            'product_code': self.ref_proveedor,
        }
        self.env['product.supplierinfo'].create(supinfo_data)

        self.update_template()

    @api.one
    def update_template(self):
        supplierinfo = self.env['product.supplierinfo'].search([('name', '=', self.supplier_id.id),
                                                                ('product_tmpl_id', '=', self.template_id.id)])

        # CAMBIAR UNIDAD DE MEDIDA EN BBDD
        if self.product_uom and self.template_id.uom_id != self.product_uom:
            new_unit = self.product_uom

            unidades_compra = self.unidades_compra if self.unidades_compra != 0 else self.template_id.purchase_uom_factor

            if unidades_compra == 1:
                new_unit_purchase = new_unit
            else:
                name = '%s %s' % (unidades_compra, new_unit.name.replace('(', '').replace(')', ''))
                new_unit_purchase = self.env['product.uom'].search([('name', '=',  name), ])
                if not new_unit_purchase:
                    uom_data = {
                        'name': name,
                        'category_id': new_unit.category_id.id,
                        'uom_type': 'bigger' if unidades_compra > 1 else 'smaller',
                        'factor': 1. / unidades_compra,
                        'rounding': 1,
                        'auto_generated': True,
                    }
                    new_unit_purchase = self.env['product.uom'].create(uom_data)

            query = 'UPDATE "product_template" SET uos_id = %s, uom_id = %s, uom_po_id = %s WHERE id = %s'\
                    % (new_unit.id, new_unit.id, new_unit_purchase.id, self.template_id.id)
            self._cr.execute(query)

            coste_compra = self.coste_compra if self.coste_compra else self.template_id.purchase_uom_price
            query = 'UPDATE "product_template" SET purchase_uom_factor = %s, purchase_uom_price = %s WHERE id = %s'\
                    % (unidades_compra, coste_compra, self.template_id.id)
            self._cr.execute(query)

            self.template_id.standard_price = coste_compra / unidades_compra

        elif self.unidades_compra > 0:
            self.template_id.purchase_uom_factor = self.unidades_compra
            self.template_id.purchase_uom_price = self.coste_compra

        # DESCRIPCION
        if self.descripcion:
            if self.import_id.description_mode == 'supplier' or self.import_id.description_mode == 'both':
                supplierinfo.product_name = self.descripcion
            if self.import_id.description_mode == 'product' or self.import_id.description_mode == 'both':
                self.template_id.name = self.descripcion

        # REF_PROVEEDOR
        if self.ref_proveedor:
            supplierinfo.product_code = self.ref_proveedor if self.ref_proveedor != '*' else None

        # DESCUENTO (DE PROVEEDOR)
        if self.descuento:
            supplierinfo.supplier_discount = self.descuento if self.descuento != '*' else None

        # EAN13
        if self.ean13:
            self.template_id.ean13 = self.ean13 if self.ean13 != '*' else None

        # CATEGORÍA
        if self.categoria:
            self.template_id.categ_id = self.categoria

        # GRUPO
        if self.grupo:
            self.template_id.group_id = self.grupo

        # MARCA
        if self.marca:
            self.template_id.brand_id = self.marca if self.marca.id != self.env.ref('sohovet_import_supplier_products.remove_brand').id else None

        # IVA COMPRA
        if self.iva_compra:
            self.template_id.supplier_taxes_id = [(6, 0, [self.iva_compra.id])]

        # IVA VENTA
        if self.iva_venta:
            self.template_id.taxes_id = [(6, 0, [self.iva_venta.id])]

        # ABASTECIMIENTOS
        if self.ubicacion:
            product_ids = [p.id for p in self.template_id.product_variant_ids]

            rules = self.env['stock.warehouse.orderpoint'].search([('product_id', 'in', product_ids),
                                                                   ('location_id', '=', self.ubicacion.id)])
            if rules:  # Actualizamos
                for rule in rules:
                    if not self.stock_min or self.stock_min == 0:
                        rule.unlink()
                    elif self.stock_min > 0:
                        rule.product_min_qty = self.stock_min
            elif self.stock_min > 0:  # Creamos nuevas
                for product_id in product_ids:
                    orderpoint_data = {
                        'product_id': product_id,
                        'warehouse_id': self._get_warehouse(self.ubicacion).id,
                        'location_id': self.ubicacion.id,
                        'product_min_qty': self.stock_min,
                        'product_max_qty': 0,
                        'qty_multiple': 1,
                    }
                    self.env['stock.warehouse.orderpoint'].create(orderpoint_data)

    @api.one
    def _get_warehouse(self, location_id):
        warehouse_ids = self.env['stock.warehouse'].search([])
        stock_locations = {warehouse.lot_stock_id: warehouse for warehouse in warehouse_ids}

        if location_id in stock_locations:
            return stock_locations[location_id]
        elif location_id.location_id:
            return self._get_warehouse(location_id.location_id)
        else:
            return None

