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
from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
import re

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    def taxes(self):
        taxes_total = {}
        for line in self.order_line:
            for tax in line.taxes_id:
                amount = tax.compute_all(line.price_unit, line.product_qty)['taxes'][0]['amount']
                if tax in taxes_total:
                    taxes_total[tax] += amount
                else:
                    taxes_total[tax] = amount

        taxes = self.order_taxes(taxes_total.keys())
        for i in range(len(taxes)):
            taxes[i] = {
                'name': 'IVA %s%%' % (int(taxes[i].amount * 100)),
                'value': ('%.2f €' % taxes_total[taxes[i]]).replace('.', ',')
            }
        return taxes

    def order_taxes(self, taxes):
        ordered_taxes = []
        for tax in taxes:
            for i in range(len(ordered_taxes)):
                if tax.amount > ordered_taxes[i].amount:
                    ordered_taxes.insert(i, tax)
                    continue
            if not tax in ordered_taxes:
                ordered_taxes.append(tax)
        return ordered_taxes

    def lines_ordered(self):
        return self.order_line.sorted(key=lambda x: x.product_id.name)