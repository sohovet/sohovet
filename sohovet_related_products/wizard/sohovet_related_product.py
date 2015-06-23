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
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError

class sohovet_related_product(models.TransientModel):
    _name = 'sohovet.related.product'

    product = fields.Many2one('product.template', 'Producto', required=True)

    units = fields.Integer('Unidades por agrupación')

    _defaults = {
        'units': 1,
    }

    @api.multi
    def save_changes(self):
        if self.units <= 1:
            raise ValidationError(_('The number of units should be greater than 1'))

        agrup_code = _(u'[Agrup]')
        unit_code = _(u'[Unid]')

        new_vals = {
            'units': self.units,
            'parent_id': self.product.id,
            'purchase_ok': False,
            'standard_price': self.product.standard_price / self.units,
            'purchase_uom_price': self.product.standard_price / self.units,
            'purchase_uom_factor': 1,
        }

        product2 = self.product.copy(new_vals)
        product2.name = self.product.name + u' ' + unit_code

        self.product.name += u' ' + agrup_code
        self.product.units = self.units
        self.product.child_id = product2

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