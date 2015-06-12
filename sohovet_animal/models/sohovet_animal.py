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
    _description = 'Specie'

    name = fields.Char('Name')

class sohovet_animal_breed(models.Model):
    _name = 'sohovet.animal.breed'
    _description = 'Breed'

    name = fields.Char('Name')

class sohovet_animal_type(models.Model):
    _name = 'sohovet.animal.type'
    _description = 'Animal type'

    _rec_name = 'code'

    code = fields.Char('Code')
    name = fields.Char('Name')

class sohovet_animal(models.Model):
    _name = 'sohovet.animal'
    _description = 'Animal'

    name = fields.Char(string='Name', required=True)
    surname = fields.Char(string='Surname', related='partner_id.lastname', readonly=True)
    specie_id = fields.Many2one('sohovet.animal.specie', string='Specie')
    breed_id = fields.Many2one('sohovet.animal.breed', string='Breed')
    type_id = fields.Many2one('sohovet.animal.type', string='Type')
    active = fields.Boolean(string='Active', default=True)
    alive = fields.Boolean(string='Alive', default=True)
    partner_id = fields.Many2one('res.partner', string='Owner', required=True, domain="[('customer', '=', True)]")
    partner_active = fields.Boolean(string='Owner active', related='partner_id.active')
