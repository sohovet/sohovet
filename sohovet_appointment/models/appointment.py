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
from datetime import datetime

class sohovet_appointment(models.Model):
    _name = 'sohovet.appointment'
    _description = 'Citas para SOHOVet'
    _rec_name = 'partner_id'
    _order = 'date_start'

    @api.multi
    def _get_current_date(self):
        return datetime.utcnow()

    partner_id = fields.Many2one('res.partner', 'Cliente')
    date_start = fields.Datetime('Fecha/hora inicial')
    date_stop = fields.Datetime('Fecha/hora final')
    date_create = fields.Datetime('Fecha de creación', default=_get_current_date)

    day = fields.Date('Fecha', compute='_get_date_time', store=True)
    initial_time = fields.Char('Hora inicial', compute='_get_date_time', store=True)
    end_time = fields.Char('Hora final', compute='_get_date_time', store=True)

    @api.one
    @api.depends('date_start', 'date_stop')
    def _get_date_time(self):
        self.day = self.date_start
        self.initial_time = self.date_start[11:-3]
        self.end_time = self.date_stop[11:-3]

