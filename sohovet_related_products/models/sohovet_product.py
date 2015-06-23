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
import openerp.addons.decimal_precision as dp
from openerp.api import Environment

########
## Product template
## - Añade marcas, ref. grupo
#######
class product_template(models.Model):
    _inherit = 'product.template'

    child_id = fields.Many2one('product.template', 'Producto unitario', readonly=True)
    parent_id = fields.Many2one('product.template', 'Producto agrupado', readonly=True)
    vinculated = fields.Boolean('Producto vinculado', compute='isRelated', store=True)
    units = fields.Integer('Unidades por agrupación')

    parent_standard_price = fields.Float(string='Precio del producto unitario', related='parent_id.standard_price')
    computed_price = fields.Float('Precio calculado', compute='computeUnitaryPrice',
                                  digits=dp.get_precision('Product Price'))
    price_updated = fields.Boolean('', compute='computeNeedsUpdate')

    parent_qty_available = fields.Float(string='Cantidad disponible (Producto agrupado)', related='parent_id.qty_available')

    @api.one
    @api.onchange('name', 'child_id', 'parent_id')
    def _set_name(self):
        agrup_code = _(u'[Agrup]')
        unit_code = _(u'[Unid]')

        if self.child_id and not self.name[-1 * len(agrup_code):] == agrup_code:  # agrup
            self.name = u'%s %s' % (self.name, agrup_code)

        if self.parent_id and not self.name[-1 * len(unit_code):] == unit_code:  # unit
            self.name = u'%s %s' % (self.name, unit_code)

    @api.one
    @api.depends('parent_id', 'child_id')
    def isRelated(self):
        self.vinculated = self.child_id.id or self.parent_id.id

    @api.one
    def removeRelated(self):
        agrup_code = _(u'[Agrup]')

        parent = self if self.child_id else self.parent_id
        child = self.child_id if self.child_id else self

        if parent.name[-1 * len(agrup_code):] == agrup_code:
            parent.name = self.name[:-1 * len(agrup_code)].strip()

        parent.child_id = False
        child.parent_id = False
        child.active = False

        return True

    @api.one
    @api.depends('parent_id', 'parent_id.standard_price')
    def computeUnitaryPrice(self):
        if self.parent_id:
            self.computed_price = self.parent_standard_price / self.units
        else:
            self.computed_price = 0

    @api.one
    def copyPrice(self):
        self.standard_price = self.computed_price


    @api.one
    def computeNeedsUpdate(self):
        self.price_updated = self.parent_id.id and self.standard_price != self.computed_price

    @api.multi
    def open_related_wizard(self):

        wizard_id = self.env['sohovet.related.product'].create({'product': self.id})

        return {'name': 'Vincular productos',
                'res_id': wizard_id.id,
                'res_model': 'sohovet.related.product',
                'target': 'new',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form'}

    @api.multi
    def open_unpack_wizard(self):
        if not self.parent_id.id and not self.child_id.id:
            return False

        if self.child_id:
            if self.qty_available < 1:
                return False

            parent_product_id = self.id
            quants_obj = self.env['stock.quant'].search([('product_id', '=', self.id)])
        elif self.parent_id:
            if self.parent_id.qty_available < 1:
                return False
            parent_product_id = self.parent_id.id
            quants_obj = self.env['stock.quant'].search([('product_id', '=', self.parent_id.id)])

        location_ids = []
        for quant in quants_obj:
            if quant.location_id.usage == 'internal':
                location_ids.append(quant.location_id.id)

        if location_ids:
            wizard_id = self.env['sohovet.related.product.unpack'].create({'product': parent_product_id,
                                                                           'location_id': location_ids[0],
                                                                           'location_dest_id': location_ids[0]})
            return {'name': 'Desempaquetar producto',
                    'res_id': wizard_id.id,
                    'res_model': 'sohovet.related.product.unpack',
                    'target': 'new',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'context': {'location_ids': location_ids}}
