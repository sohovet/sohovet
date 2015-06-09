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

STATUS_VALUES = {
    ('appointment', 'Pide cita'),
    ('extern', 'Vacunado en otro centro'),
    ('lost', 'Propietario dado de baja'),
    ('extern', 'Animal/es dados de baja'),
    ('unreachable', 'Imposible contactar'),
    ('stop_calling', 'No volver a llamar'),
}

class sohovet_vacine_call_reminder(models.Model):
    _name = 'sohovet.vaccine.call_reminder'
    _description = 'Llamada de recordatorio'
    _rec_name = 'partner_id'
    _order = 'id DESC'

    status = fields.Selection(STATUS_VALUES, 'Resultado', required=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', required=True)
    date = fields.Datetime('Fecha', default=fields.Datetime.now(), required=True)
    sms_reminder_id = fields.Many2one('sohovet.vaccine.reminder', 'Recordatorio', required=True)
    notes = fields.Text('Notas')

    @api.model
    def create(self, vals):
        res = super(sohovet_vacine_call_reminder, self).create(vals)

        reminder_ids = self.env['sohovet.vaccine.reminder'].search([('partner_id', '=', res.partner_id.id),
                                                                    ('state', '=', 'draft')])
        for reminder in reminder_ids:
            reminder.state = 'cancel'

        return res

class sohovet_vaccine_reminder_batch(models.Model):
    _inherit = 'sohovet.vaccine.reminder.batch'

    calls_remaining = fields.Integer('Llamadas pendientes')

    @api.model
    def create(self, vals):
        res = super(sohovet_vaccine_reminder_batch, self).create(vals)
        res.calls_remaining = len(res.reminder_ids)
        return res

class sohovet_vacine_reminder(models.Model):
    _inherit = 'sohovet.vaccine.reminder'

    call_reminder_ids = fields.One2many('sohovet.vaccine.call_reminder', 'sms_reminder_id', 'Llamadas')
    n_calls = fields.Integer('Llamadas', compute='_get_n_calls')

    @api.one
    @api.depends('call_reminder_ids')
    def _get_n_calls(self):
        self.n_calls = len(self.call_reminder_ids)



    @api.multi
    def register_call(self):
        context = {
            'default_partner_id': self.partner_id.id,
            'default_sms_reminder_id': self.id,
        }

        action = {
            'name': 'Registrar llamada',
            'type': 'ir.actions.act_window',
            'res_model': 'sohovet.vaccine.call_reminder',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
        }
        return action

    @api.multi
    def remove_calls(self):
        calls = self.env['sohovet.vaccine.call_reminder'].search([('sms_reminder_id', '=', self.id)])
        for call in calls:
            call.unlink()

class res_partner(models.Model):
    _inherit = 'res.partner'

    call_ids = fields.One2many('sohovet.vaccine.call_reminder', 'partner_id', 'Llamadas')

    @api.multi
    def register_call(self):
        if not self.reminder_ids:
            raise ValidationError('No se puede registrar una llamada sin un recordatorio previo')
        context = {
            'default_sms_reminder_id': self.reminder_ids[0].id,
            'default_partner_id': self.id,
        }

        action = {
            'name': 'Registrar llamada',
            'type': 'ir.actions.act_window',
            'res_model': 'sohovet.vaccine.call_reminder',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
        }
        return action
