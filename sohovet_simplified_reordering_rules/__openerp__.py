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
    'name': 'SOHOVet simplified reordering rules',
    'version': '1.0',
    'category': 'Productos',
    'description': """Módulo que simplifica las reglas de reabastecimiento""",
    'author': 'Juan Ignacio Alonso Barba',
    'website': 'http://www.enzo.es/',
    'license': 'AGPL-3',
    'depends': ['purchase', 'sale'],
    'data': [
        'views/sohovet_orderpoint.xml',
        'views/sohovet_product_view.xml',
    ],
    'active': False,
    'installable': True,
}
