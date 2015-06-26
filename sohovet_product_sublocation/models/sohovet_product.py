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

from openerp import fields, models, api, SUPERUSER_ID, _
from openerp.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sublocation_ids = fields.Many2many('stock.sublocation', string='Sublocations')

    @api.constrains('sublocation_ids')
    def _check_sublocation_ids(self):
        locations = self.sublocation_ids.mapped('location_id')
        if len(locations) != len(self.sublocation_ids):
            raise ValidationError(_('One product can not be in two differents sublocations of the same location. '
                                    'Check sublocations'))

    def sublocations(self, location_id):
        sublocations = self.sublocation_ids.filtered(lambda r: r.location_id == location_id)
        return sublocations


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def sublocations(self, location_id):
        sublocations = self.product_tmpl_id.sublocation_ids.filtered(lambda r: r.location_id == location_id)
        print sublocations
        return sublocations
