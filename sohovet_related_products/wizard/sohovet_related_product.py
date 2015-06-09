# -*- encoding: utf-8 -*-
##############################################################################
#                                                                            #
#  OpenERP, Open Source Management Solution.                                 #
#                                                                            #
#  @author Juan Ignacio Alonso-Barba <jialonso@grupovermon.com>               #
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

class sohovet_related_product(models.TransientModel):
    _name = 'sohovet.related.product'

    product1 = fields.Many2one('product.template', 'Producto 1',
                               domain="[('vinculated', '=', False), ('id', '!=', product2)]", required=True)
    product2 = fields.Many2one('product.template', 'Producto 2',
                               domain="[('vinculated', '=', False), ('id', '!=', product1)]")

    product1_unitary = fields.Boolean('Es un producto unitario')

    units = fields.Integer('Unidades por agrupación')
    update_price = fields.Boolean('Actualizar ahora el precio de coste del producto unitario')

    _defaults = {
        'product1_unitary': True,
        'update_price': True,
        'units': 1,
    }

    @api.multi
    def save_changes(self):
        if self.units <= 1:
            raise ValidationError('El número de unidades debe ser mayor que 1')
        if not self.product2.id:
            raise ValidationError('Introduce el segundo producto')

        if self.product1_unitary:
            self.product1.parent_id = self.product2
            self.product2.child_id = self.product1
            if self.update_price:
                self.product1.standard_price = round(self.product2.standard_price / self.units, 2)
        else:
            self.product1.child_id = self.product2
            self.product2.parent_id = self.product1
            if self.update_price:
                self.product2.standard_price = round(self.product1.standard_price / self.units, 2)

        self.product1.units = self.units
        self.product2.units = self.units

        return {'type': 'ir.actions.act_window_close'}

class sohovet_related_product_unpack(models.TransientModel):
    _name = 'sohovet.related.product.unpack'

    product = fields.Many2one('product.template', 'Producto', required=True)
    location_id = fields.Many2one('stock.location', 'Ubicación de origen', domain=[('usage', '=', 'internal')],
                                  required=True)
    location_dest_id = fields.Many2one('stock.location', 'Ubicación de destino', domain=[('usage', '=', 'internal')],
                                       required=True)

    @api.onchange('location_id')
    def on_change_location(self):
        if not self.location_dest_id:
            self.location_dest_id = self.location_id

    @api.one
    def unpack(self):
        if self.product.qty_available <= 0:
            pass  # ERROR!
        stock_move_data = {
            'name': 'Desagrupar: %s' % self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'product_uom': self.product.uom_id.id,
            'invoice_state': 'none',
            'location_id': self.location_id.id,
            'location_dest_id': self.env.ref('sohovet_related_products.unpacked_items_vl').id
        }
        stock_move_obj = self.env['stock.move'].create(stock_move_data)
        stock_move_obj.action_done()

        stock_move_data = {
            'name': 'Desagrupar: %s' % self.product.name,
            'product_id': self.product.child_id.id,
            'product_uom_qty': self.product.units,
            'product_uom': self.product.child_id.uom_id.id,
            'invoice_state': 'none',
            'location_id': self.env.ref('sohovet_related_products.unpacked_items_vl').id,
            'location_dest_id': self.location_dest_id.id,
        }
        stock_move_obj = self.env['stock.move'].create(stock_move_data)
        stock_move_obj.action_done()

        return {'type': 'ir.actions.act_window_close'}