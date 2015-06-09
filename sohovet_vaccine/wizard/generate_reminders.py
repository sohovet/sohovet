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
from datetime import datetime, timedelta
import calendar

class sohovet_vaccine_reminder_wizard(models.TransientModel):
    _name = 'sohovet.vaccine.reminder.wizard'

    @api.multi
    def _get_init_date(self):
        now = datetime.now()
        day = 1
        month = now.month
        year = now.year
        return datetime(year, month, day)

    @api.multi
    def _get_end_date(self):
        now = datetime.now()
        month = now.month
        year = now.year
        day = calendar.monthrange(year, month)[1]
        return datetime(year, month, day)

    @api.multi
    def _get_default_last_reminder_min_date(self):
        now = datetime.now()
        day = 1
        month = now.month - 1
        year = now.year
        if month <= 0:
            month = month + 12
            year = year - 1
        return datetime(year, month, day)

    @api.multi
    def _get_default_last_reminder_max_date(self):
        now = datetime.now()
        month = now.month - 1
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
        day = calendar.monthrange(year, month)[1]
        return datetime(year, month, day)

    @api.multi
    def _is_updated_48h(self):
        dt_format = '%Y-%m-%d %H:%M:%S'

        config = self.env['ir.config_parameter']
        date_str = config.get_param('connector.last_update')

        if not date_str:
            return False

        last_date = datetime.strptime(date_str, dt_format)
        current_date = datetime.utcnow()

        return current_date - last_date < timedelta(hours=48)

    init_date = fields.Date('Fecha inicial', required=True, default=_get_init_date)
    end_date = fields.Date('Fecha final', required=True, default=_get_end_date)
    type = fields.Selection([('first', 'Primer recordatorio'), ('other', 'Recordatorios de repesca')],
                            'Tipo de recordatorios', default='first', required=True)
    max_sent_reminders = fields.Integer('Número máximo de recordatorios anteriores', default=1, required=True)
    last_reminder_min_date = fields.Date('Fecha mínima del último recordatorio', default=_get_default_last_reminder_min_date, required=True)
    last_reminder_max_date = fields.Date('Fecha máxima del último recordatorio', default=_get_default_last_reminder_max_date, required=True)
    updated_48h = fields.Boolean('Sincronizados en las últimas 48h.', required=True, readonly=True, default=_is_updated_48h)

    @api.multi
    def generate_reminders(self):
        # Borrar recordatorios en borrador
        draft_reminders = self.env['sohovet.vaccine.reminder'].search([('state', 'in', ['draft', 'incomplete'])])
        for reminder in draft_reminders:
            reminder.unlink()
            # reminder.state = 'cancel'

        # Generar recordatorios nuevos
        if self.type == 'first':
            search_data = [
                ('animal_active', '=', True),
                ('partner_active', '=', True),
                ('animal_alive', '=', True),
                ('next_type_id', '!=', False),
                ('next_vaccine', '=', False),
                ('date_next_computed', '>=', self.init_date),
                ('date_next_computed', '<=', self.end_date),
                ('num_sent_reminders', '=', 0),
            ]
        elif self.type == 'other':
            search_data = [
                ('animal_active', '=', True),
                ('partner_active', '=', True),
                ('animal_alive', '=', True),
                ('next_type_id', '!=', False),
                ('next_vaccine', '=', False),
                ('last_reminder_date', '>=', self.last_reminder_min_date),
                ('last_reminder_date', '<=', self.last_reminder_max_date),
                ('num_sent_reminders', '>', 0),
                ('num_sent_reminders', '<=', self.max_sent_reminders),
            ]

        vaccines = self.env['sohovet.vaccine'].search(search_data)

        ## DOUBLE CHECK!!
        if vaccines:
            quick_updater = self.env['sohovet.connector.quick.update'].create({})
            quick_updater.update_partners([vaccine.animal_id.partner_id for vaccine in vaccines])
            quick_updater.update_animals([vaccine.animal_id for vaccine in vaccines])
            quick_updater.update_vaccines([vaccine for vaccine in vaccines])

            vaccines = self.env['sohovet.vaccine'].search(search_data)
        ###########

        prop = {}
        for vaccine in vaccines:
            # if not vaccine.animal_id.partner_id.mobile:
            #     continue
            id_partner = vaccine.animal_id.partner_id.id
            if id_partner in prop:
                prop[id_partner].append(vaccine)
            else:
                prop[id_partner] = [vaccine]

        for id_partner in prop:
            reminder_data = {
                'type': self.type,
                'partner_id': id_partner,
                'vaccine_ids': [(6, 0, [vaccine.id for vaccine in prop[id_partner]])],
            }
            self.env['sohovet.vaccine.reminder'].create(reminder_data)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }