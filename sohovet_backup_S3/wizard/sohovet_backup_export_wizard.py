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

class sohovetExportProductsWizard(models.TransientModel):
    _name = 'sohovet.backup.export.wizard'
    _description = 'Exportar productos'
    _transient_max_count = 1
    _transient_max_hours = 0.1  # 6 minutes

    data = fields.Binary(string='File')
    name = fields.Char(string='File name')

    @api.multi
    def open(self):
        action = {
            'name': 'Descargar backup',
            'type': 'ir.actions.act_window',
            'res_model': 'sohovet.backup.export.wizard',
            'res_id': self.ids[0],
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }
        return action
