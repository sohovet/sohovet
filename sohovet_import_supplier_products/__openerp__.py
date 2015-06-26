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

{
    'name': 'SOHOVet import/export supplier products',
    'version': '1.0',
    'category': 'Productos',
    'description': """Módulo que permite la importación y exportación de productos por proveedor.""",
    'author': 'Juan Ignacio Alonso Barba',
    'website': 'http://www.enzo.es/',
    'license': 'AGPL-3',
    'depends': [
        'product',
        'sohovet_product',
        'sohovet_stock_sublocation',
        'sohovet_product_price',
    ],
    'data': [
        'data/sohovet_remove_fields.xml',
        'views/sohovet_import_products.xml',
        'views/sohovet_res_partner_view.xml',
        'views/sohovet_product_view.xml',
        'wizard/sohovet_import_products_wizard.xml',
        'wizard/sohovet_export_products_wizard.xml',
        'wizard/sohovet_export_products_wizard.xml',
        'security/ir.model.access.csv',
    ],
    'active': False,
    'installable': True,
}
