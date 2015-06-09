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

class sohovetStockReport(models.TransientModel):
    _name = 'sohovet.stock.report'
    _description = 'Stock report wizard'

    check = fields.Boolean('Sólo stock mímimo > 0')
    item_ids = fields.One2many('sohovet.stock.report.item', 'report_id')
    supplier_ids = fields.Many2many('res.partner', compute='_get_suppliers')

    @api.model
    def default_get(self, fields):
        res = super(sohovetStockReport, self).default_get(fields)
        template_ids = self.env['product.template'].browse(self.env.context['active_ids'])
        item_ids = []
        for template_id in template_ids:
            product_ids = [product.id for product in template_id.product_variant_ids]
            stock_rules_ids = self.env['stock.warehouse.orderpoint'].search([('product_id', 'in', product_ids)])
            if stock_rules_ids:
                for stock_rule in stock_rules_ids:
                    quants_ids = self.env['stock.quant'].search([('product_id', '=', stock_rule.product_id.id),
                                                                 ('location_id', '=', stock_rule.location_id.id)])

                    qty_available = 0
                    for quant in quants_ids:
                        qty_available += quant.qty

                    item_data = {
                        # 'report_id': self.id,
                        'can_change_name': False,
                        'name': stock_rule.product_id.id,
                        'qty_available': qty_available,
                        'supplier_id': stock_rule.product_id.seller_id.id,
                        'ubication': stock_rule.warehouse_id.id,
                        'qty_min': int(stock_rule.product_min_qty),
                        'stock_rule': stock_rule.id,
                    }
                    item_ids.append(item_data)
            elif 'stock_full_report' in self.env.context:
                for product_id in template_id.product_variant_ids:
                    locations = {}
                    quants_ids = self.env['stock.quant'].search([('product_id', '=', product_id.id)])

                    for quant in quants_ids:
                        if quant.location_id.id in locations:
                            locations[quant.location_id.id] += quant.qty
                        else:
                            locations[quant.location_id.id] = quant.qty

                    if locations:
                        for id_location in locations:
                            id_warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', id_location)])
                            if id_warehouse and locations[id_location] != 0:
                                item_data = {
                                    # 'report_id': self.id,
                                    'name': product_id.id,
                                    'qty_available': locations[id_location] or 0,
                                    'supplier_id': product_id.seller_id.id,
                                    'ubication': id_warehouse[0],
                                    'qty_min': 0,
                                }
                                item_ids.append(item_data)
                    else:
                        item_data = {
                            # 'report_id': self.id,
                            'can_change_name': False,
                            'name': product_id.id,
                            'qty_available': int(product_id.qty_available) or 0,
                            'supplier_id': product_id.seller_id.id or
                                           (hasattr(product_id, 'parent_id') and product_id.parent_id.seller_id.id),
                            'qty_min': 0,
                        }
                        item_ids.append(item_data)
        res.update({'item_ids': item_ids})
        return res

    @api.one
    def _get_suppliers(self):
        supplier_ids = [item.supplier_id.id for item in self.item_ids]
        self.supplier_ids = list(set(supplier_ids))

    @api.multi
    def print_report(self):
        return self.env['report'].get_action(self, 'sohovet_stock_report.informe_stock')

    @api.multi
    def save(self):
        for item in self.item_ids:
            if not item.ubication:
                continue
            update_stock_data = {
                'product_id': item.name.id,
                'new_quantity': item.qty_available,
                'location_id': item.ubication.lot_stock_id.id,
            }
            update_stock_wizard = self.env['stock.change.product.qty'].create(update_stock_data)
            update_stock_wizard.change_product_qty()

            # Updates also min_stock
            if item.qty_min:
                if item.stock_rule:
                    if item.qty_min != int(item.stock_rule.product_min_qty):
                        item.stock_rule.product_min_qty = item.qty_min
                    if item.ubication != item.stock_rule.warehouse_id:
                        item.stock_rule.warehouse_id = item.ubication
                else:
                    orderpoint_data = {
                        'product_id': item.name.id,
                        'warehouse_id': item.ubication.id,
                        'location_id': item.ubication.lot_stock_id.id,
                        'product_min_qty': item.qty_min,
                        'product_max_qty': 0,
                        'qty_multiple': 1,
                    }
                    self.env['stock.warehouse.orderpoint'].create(orderpoint_data)
            elif item.stock_rule:
                item.stock_rule.unlink()

class sohovetStockReportItem(models.TransientModel):
    _name = 'sohovet.stock.report.item'

    report_id = fields.Many2one('sohovet.stock.report', 'Informe')
    stock_rule = fields.Many2one('stock.warehouse.orderpoint', 'Regla de reabastecimiento')
    name = fields.Many2one('product.product', 'Producto')
    can_change_name = fields.Boolean(default=True)
    qty_min = fields.Integer('Stock mínimo')
    qty_available = fields.Integer('Stock actual')
    qty_purchase = fields.Integer('Unidades compra', related='name.purchase_uom_factor')
    ubication = fields.Many2one('stock.warehouse', 'Ubicación')
    supplier_id = fields.Many2one('res.partner', 'Proveedor')

    # @api.one
    # def duplicate(self):
    #     vals = {
    #         'report_id': self.report_id.id,
    #         'name': self.name.id,
    #         'supplier_id': self.supplier_id.id,
    #         'qty_min': 0,
    #         'qty_available': 0,
    #         'ubication': None,
    #     }
    #     self.create(vals)