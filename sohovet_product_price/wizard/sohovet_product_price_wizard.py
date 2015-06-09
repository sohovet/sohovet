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
from openerp.exceptions import ValidationError
import re

class sohovet_product_price_wizard(models.TransientModel):
    _name = 'sohovet.product.price.wizard'

    categ_id = fields.Many2one('product.category', 'Category', default=None, domain="[('type', '=', 'normal')]")
    category_margin = fields.Integer('Category margin (%)', related='categ_id.category_margin', readonly=True)
    additional_margin = fields.Char('Additional margin (%)', default=None, size=3)
    total_margin = fields.Char('Total margin (%)', compute="_get_total_margin")
    discount_percentage = fields.Char('Discount (%)', default=None, size=2)

    @api.depends('category_margin')
    @api.onchange('categ_id', 'additional_margin')
    def _get_total_margin(self):
        if self.categ_id and self.additional_margin and re.match('^-?[0-9]+', self.additional_margin):
            add_margin = int(self.additional_margin)
            total_margin = add_margin + self.category_margin
            self.total_margin = str(total_margin) if 0 <= total_margin < 100 else ''
        else:
            self.total_margin = ''


    @api.depends('category_margin')
    @api.constrains('additional_margin')
    def _check_additional_margin(self):
        if self.additional_margin:
            if not re.match('^-?[0-9]+', self.additional_margin):
                raise ValidationError(_('Additional_margin should be a number between -99 and 99'))
            elif int(self.additional_margin) > 99:
                raise ValidationError(_('Additional_margin should be a number between -99 and 99'))
            elif self.categ_id:
                total_margin = int(self.additional_margin) + self.category_margin
                if not 0 <= total_margin < 100:
                    raise ValidationError(_('Total margin should be a number between 0 and 99'))


    @api.constrains('discount_percentage')
    def _check_discount(self):
        if self.discount_percentage and not self.discount_percentage.isdigit():
            raise ValidationError(_('Discount should be a number between 0 and 99'))

    @api.multi
    def apply_changes(self):
        ids = self.env.context['active_ids']
        templates = self.env['product.template'].search([('id', 'in', ids)])
        for template in templates:
            if self.categ_id:
                template.categ_id = self.categ_id
                template._compute_total_margin()
                if not template.fixed_price:
                    template._compute_fixed_price_with_margin()
                template._recompute_prices()
            if self.additional_margin:
                template.fixed_price = False
                template.additional_margin = int(self.additional_margin)
            if self.discount_percentage:
                template.discount_percentage = int(self.discount_percentage)
                template._recompute_prices()

