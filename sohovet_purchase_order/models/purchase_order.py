# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api
import re

pattern = re.compile('^\[.*\]')

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    allowed_products = fields.Many2many(comodel_name='product.product', string='Allowed products')

    @api.multi
    def onchange_partner_id(self, partner_id):
        result = super(PurchaseOrder, self).onchange_partner_id(partner_id)
        result['value']['allowed_products'] = ([x.id for x in self.get_allowed_products(partner_id)])
        return result

    @api.multi
    def get_allowed_products(self, partner_id):
        product_obj = self.env['product.product']
        allowed_products = product_obj.search([('purchase_ok', '=', True)])
        if partner_id:
            partner_obj = self.env['res.partner'].browse(partner_id)
            cond = [('name', 'in', (partner_id, partner_obj.commercial_partner_id.id))]
            supplierinfos = self.env['product.supplierinfo'].search(cond)
            allowed_products = product_obj.search([('product_tmpl_id', 'in',
                                                    [x.product_tmpl_id.id for x in supplierinfos])])
        return allowed_products


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Char('Discount')

    desc_product_code = fields.Char('Código del producto', compute='_split_description', store=True,
                                    readonly=False)
    desc_product_name = fields.Char('Nombre del producto', compute='_split_description', store=True,
                                    readonly=False)

    @api.one
    @api.depends('name')
    def _split_description(self):
        if self.name:
            match = pattern.match(self.name)
            if match:
                self.desc_product_code = match.group(0)[1:-1]
                self.desc_product_name = self.name[len(self.desc_product_code)+2:].strip()
            else:
                self.desc_product_code = ''
                self.desc_product_name = self.name

    @api.multi
    def onchange_product_id(self, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft'):

        res = super(PurchaseOrderLine, self).onchange_product_id(pricelist_id, product_id, qty, uom_id,
            partner_id, date_order, fiscal_position_id, date_planned, name, price_unit, state)

        discount = None
        product = self.env['product.product'].browse(product_id)
        for supplier in product.seller_ids:
            if partner_id and (supplier.name.id == partner_id):
                supplierinfo = supplier
                if supplierinfo.supplier_discount:
                    discount = supplierinfo.supplier_discount

        if product.purchase_uom_price:
            res['value'].update({'price_unit': product.purchase_uom_price})
        if discount:
            res['value'].update({'discount': discount})
        return res