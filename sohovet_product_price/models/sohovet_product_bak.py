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
import openerp.addons.decimal_precision as dp
import re

########
## Product template
## - Añade margen
#######
class product_category(models.Model):
    _inherit = 'product.category'

    category_margin = fields.Integer('Category margin (%)', inverse='_set_category_margin')

    @api.one
    def _set_category_margin(self):
        templates = self.env['product.template'].search([('categ_id', '=', self.id)])
        for template in templates:
            template._compute_total_margin()
            if not template.fixed_price:
                template._compute_fixed_price_with_margin()
                template._recompute_prices()


    @api.constrains('category_margin')
    def _check_margin(self):
        if not 0 <= self.category_margin < 100:
            raise ValidationError(_('Category margin should be a number between 0 and 99'))
        templates = self.env['product.template'].search([('categ_id', '=', self.id)])
        for template in templates:
            product_margin = self.category_margin + template.additional_margin
            if not 0 <= product_margin < 100:
                raise ValidationError(_('Can not set category margin.'
                                        ' Some products of the category have an invalid total margin'))

    @api.multi
    def open_category(self):
        return {'res_id': self.id,
                'res_model': 'product.category',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
        }

    @api.multi
    def open_products_in_category(self):
        view = self.env.ref('sohovet_product_price.set_pvp_action')
        return view


        # return {'name': 'Sell prices',
        #         'res_model': 'product.template',
        #         'type': 'ir.actions.act_window',
        #         'view_mode': 'tree',
        #         'view_type': 'form',
        #         'domain': [('categ_id', '=', self.id)],
        #         'view_id': self.env.ref('sohovet_product_price.set_pvp_tree_view').id,
        #         'search_view_id': self.env.ref('sohovet_product_price.sohovet_set_pvp_search_view').id,
        # }


class product_template(models.Model):
    _inherit = 'product.template'

    standard_price = fields.Float(inverse='_set_cost_price')
    standard_price2 = fields.Float('Cost price', related='standard_price')

    taxes_percentage = fields.Float('Taxes percentage (%)', compute='_compute_taxes_percentage', digits=(2, 0))

    fixed_price = fields.Boolean('Fixed price', default=False)

    # MARGIN (int)
    category_margin = fields.Integer('Category margin (%)', related='categ_id.category_margin', store=True)
    additional_margin = fields.Integer('Additional margin (%)', inverse='_set_additional_margin')
    total_margin = fields.Integer('Total margin (%)', compute='_compute_total_margin', store=True)

    fixed_price_value = fields.Char('Fixed price', compute='_get_fixed_price_value', inverse='_set_fixed_price_value', store=False)

    default_sell_price = fields.Float('Default sell price', digits=dp.get_precision('Product Price'), inverse='_recompute_prices')

    default_sell_price_plus_taxes = fields.Float('Default sell price with taxes', digits=dp.get_precision('Product Price'), store=True)

    discount_str = fields.Char('Discount (%)', compute="_get_discount_str", inverse='_set_discount_str', store=False, size=2)
    discount_percentage = fields.Integer('Discount (%)')

    list_price_plus_taxes = fields.Float('Sell price with taxes (€)', digits=dp.get_precision('Product Price'), store=True)

    real_margin = fields.Float('Real margin (€)', compute='_compute_margins', digits=dp.get_precision('Product Price'), store=True)
    real_margin_percentage = fields.Float('Real margin (%)', compute='_compute_margins', digits=(2, 1), store=True)

    name = fields.Char(translate=False)
    categ_name = fields.Char('Category', related='categ_id.name')

    @api.one
    @api.onchange('standard_price')
    def _set_cost_price(self):
        if not self.fixed_price:
            self._compute_fixed_price_with_margin()
        self._recompute_prices()


    @api.onchange('fixed_price_value')
    def _set_fixed_price_value(self):
        if self.fixed_price_value and not re.match('^[0-9]+[.,]?[0-9]*$', self.fixed_price_value):
            raise ValidationError(_('Fixed price value should be a positive number'))
        if self.fixed_price_value:
            self.fixed_price = True
            value = float(self.fixed_price_value.replace(',', '.'))
            self.default_sell_price = value
            # self.fixed_price_value = ('%.2f' % self.default_sell_price).replace('.', ',')
        else:
            self.fixed_price = False
            self._compute_fixed_price_with_margin()
        # self._recompute_prices()

    @api.onchange('fixed_price')
    def _on_change_fixed_price(self):
        if not self.fixed_price:
            self._compute_fixed_price_with_margin()

    @api.one
    @api.onchange('default_sell_price')
    def _get_fixed_price_value(self):
        if self.fixed_price:
            self.fixed_price_value = ('%.2f' % self.default_sell_price).replace('.', ',')
        else:
            self.fixed_price_value = ''

    @api.one
    @api.depends('category_margin')
    def _compute_total_margin(self):
        total_margin = self.category_margin + self.additional_margin
        if not 0 <= total_margin < 100:
            raise ValidationError(_('Total margin should be a number between 0 and 99'))
        self.total_margin = self.category_margin + self.additional_margin

    @api.one
    @api.onchange('additional_margin')
    def _set_additional_margin(self):
        self._compute_total_margin()
        self._compute_fixed_price_with_margin()
        # self._recompute_prices()


    @api.one
    @api.depends('total_margin')
    def _compute_fixed_price_with_margin(self):
        self.default_sell_price = self.standard_price / (1 - self.total_margin/100.)

    @api.one
    def _get_discount_str(self):
        if self.discount_percentage == 0:
            self.discount_str = ''
        else:
            self.discount_str = str(self.discount_percentage)

    @api.one
    def _set_discount_str(self):
        if self.discount_str:
            if not self.discount_str.isdigit():
                raise ValidationError(_('Discount should be a number between 0 and 99'))
            self.discount_percentage = int(self.discount_str)
        else:
            self.discount_percentage = 0
        self._recompute_prices()


    @api.one
    @api.onchange('taxes_id')
    def _compute_taxes_percentage(self):
        percentage = 0.0
        for tax in self.taxes_id:
            if not tax.price_include and tax.type == 'percent':
                percentage += tax.amount
        self.taxes_percentage = percentage * 100


    @api.one
    @api.depends('taxes_percentage', 'standard_price')
    @api.onchange('default_sell_price', 'discount_percentage')
    def _recompute_prices(self):
        if self.default_sell_price:
            default_sell_price_plus_taxes = self.default_sell_price * (1 + self.taxes_percentage/100.)
            list_price = self.default_sell_price * (1 - self.discount_percentage/100.)
            list_price_plus_taxes = list_price * (1 + self.taxes_percentage/100.)

            if default_sell_price_plus_taxes != self.default_sell_price_plus_taxes:
                self.default_sell_price_plus_taxes = default_sell_price_plus_taxes
            if list_price != self.list_price:
                self.list_price = list_price
            if list_price_plus_taxes != self.list_price_plus_taxes:
                self.list_price_plus_taxes = list_price_plus_taxes
        self._compute_margins()


    @api.one
    @api.depends('standard_price')
    @api.onchange('default_sell_price')
    def _compute_margins(self):
        self.real_margin = (self.list_price - self.standard_price)
        self.real_margin_percentage = self.real_margin / self.list_price * 100 if self.list_price != 0 else 0

    @api.one
    @api.depends('taxes_percentage')
    @api.onchange('default_sell_price_plus_taxes')
    def _set_default_sell_price_plus_taxes(self):
        default_sell_price = self.default_sell_price_plus_taxes / (1 + self.taxes_percentage/100.)
        if default_sell_price != self.default_sell_price:
            self.default_sell_price = default_sell_price
            # self._recompute_prices()


    @api.one
    @api.depends('taxes_percentage')
    @api.onchange('list_price')
    def _set_list_price(self):
        default_sell_price = self.list_price / (1 - self.discount_percentage/100.)
        if default_sell_price != self.default_sell_price:
            self.default_sell_price = default_sell_price
            # self._recompute_prices()

    @api.one
    @api.depends('taxes_percentage')
    @api.onchange('list_price_plus_taxes')
    def _set_list_price_plus_taxes(self):
        list_price = self.list_price_plus_taxes / (1 + self.taxes_percentage/100.)
        default_sell_price = list_price / (1 - self.discount_percentage/100.)
        if default_sell_price != self.default_sell_price:
            self.default_sell_price = default_sell_price
            # self._recompute_prices()

    @api.multi
    def open_template(self):
        # print 'open_template %s' % self.id
        return {'res_id': self.id,
                'res_model': 'product.template',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
        }

    @api.multi
    def open_category(self):
        # print 'open_category %s' % self.categ_id.id
        return {'res_id': self.categ_id.id,
                'res_model': 'product.category',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
        }