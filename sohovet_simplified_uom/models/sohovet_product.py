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
import openerp.addons.decimal_precision as dp

class product_template(models.Model):
    _inherit = 'product.template'

    purchase_uom_factor = fields.Integer('Unidades de compra', inverse='_set_purchase_uom_factor', required=True, default=1)
    purchase_uom_price = fields.Float('Coste total (sin IVA)', inverse='_set_purchase_uom_price', digits=dp.get_precision('Product Price'))
    uom_id = fields.Many2one('product.uom', inverse='_set_purchase_uom_factor')

    @api.one
    def _set_purchase_uom_factor(self):
        if self.purchase_uom_factor == 1:
            self.uom_po_id = self.uom_id
        else:
            name = '%s %s' % (self.purchase_uom_factor, self.uom_id.name.replace('(', '').replace(')', ''))
            if not self.uom_po_id or self.uom_po_id.name != name:
                uom_po_id = self.env['product.uom'].search([('name', '=',  name), ])
                if not uom_po_id:
                    uom_po_id_data = {
                        'name': name,
                        'category_id': self.uom_id.category_id.id,
                        'uom_type': 'bigger' if self.purchase_uom_factor > 1 else 'smaller',
                        'factor': 1. / self.purchase_uom_factor,
                        'rounding': 1,
                        'auto_generated': True,
                    }
                    uom_po_id = self.env['product.uom'].create(uom_po_id_data)
                self.uom_po_id = uom_po_id

    @api.one
    @api.onchange('purchase_uom_price', 'purchase_uom_factor')
    def _set_purchase_uom_price(self):
        if self.purchase_ok:
            self.standard_price = self.purchase_uom_price / self.purchase_uom_factor

class product_uom(models.Model):
    _inherit = 'product.uom'

    auto_generated = fields.Boolean('Auto generated', default=False)