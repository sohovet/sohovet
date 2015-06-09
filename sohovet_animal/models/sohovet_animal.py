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

class sohovet_animal_specie(models.Model):
    _name = 'sohovet.animal.specie'
    _description = 'Especie de animal'

    name = fields.Char('Nombre')

class sohovet_animal_breed(models.Model):
    _name = 'sohovet.animal.breed'
    _description = 'Raza de animal'

    name = fields.Char('Nombre')

class sohovet_animal_type(models.Model):
    _name = 'sohovet.animal.type'
    _description = 'Tipo de animal'

    _rec_name = 'code'

    code = fields.Char('Código')
    name = fields.Char('Nombre')

class sohovet_animal(models.Model):
    _name = 'sohovet.animal'
    _description = 'Animal'

    name = fields.Char('Nombre', required=True)
    surname = fields.Char('Apellidos')
    specie_id = fields.Many2one('sohovet.animal.specie', 'Especie')
    breed_id = fields.Many2one('sohovet.animal.breed', 'Raza')
    type_id = fields.Many2one('sohovet.animal.type', 'Tipo')
    active = fields.Boolean('Activo', default=True)
    alive = fields.Boolean('Vivo', default=True)
    partner_id = fields.Many2one('res.partner', 'Propietario', required=True, domain="[('customer', '=', True)]")
    partner_active = fields.Boolean('Propietario activo', related='partner_id.active')

    @api.one
    @api.onchange('partner_id')
    def _on_change_partner_id(self):
        self.surname = self.partner_id.apellidos