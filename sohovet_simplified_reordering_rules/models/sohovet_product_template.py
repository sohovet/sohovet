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

from openerp import fields, models, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def action_open_orderpoint(self):
        product_ids = [variant.id for variant in self.product_variant_ids]
        context = {'product_ids': product_ids}

        if len(product_ids) == 1:
            context['default_product_id'] = product_ids[0]

        warehouse_ids = self.env['stock.warehouse'].search([])
        if len(warehouse_ids) == 1:
            context['default_warehouse_id'] = warehouse_ids[0].id

        action = {
            'name': _('Reordering rules'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.warehouse.orderpoint',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref('sohovet_simplified_reordering_rules.sohovet_warehouse_orderpoint_editable_tree').id,
            'context': context,
            'domain': [('product_id', 'in', product_ids)],
        }
        return action
