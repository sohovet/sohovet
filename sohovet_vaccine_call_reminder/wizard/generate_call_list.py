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

class sohovet_vacine_call_list_wizard(models.Model):
    _name = 'sohovet.vaccine.call_reminder.wizard'
    _description = 'Asistente para generar lista de llamadas'

    @api.multi
    def _batch_domain(self):
        today = fields.Date.from_string(fields.Date.today())
        week_ago = today - timedelta(7)
        return [('calls_remaining', '>', 0), ('type', '=', 'other'), ('date', '<', fields.Date.to_string(week_ago))]

    batch = fields.Many2one('sohovet.vaccine.reminder.batch', 'Lote', required=True, domain=_batch_domain)
    exclude_unreachable = fields.Boolean('Excluir clientes "Imposible contactar"', default=False)
    n_items = fields.Integer('Clientes a llamar', compute='_get_n_items')

    @api.one
    @api.depends('batch', 'exclude_unreachable')
    def _get_n_items(self):
        if not self.batch:
            self.n_items = 0
            return
        list_of_ids = []
        for reminder in self.batch.reminder_ids:
            # Siguiente vacuna
            ignore_cliente = False
            for vaccine in reminder.vaccine_ids:
                if vaccine.next_vaccine:
                    ignore_cliente = True

            if ignore_cliente:
                continue

            # Citas
            search_queue = [
                ('partner_id', '=', reminder.partner_id.id),
                ('date_create', '>=', reminder.date)
            ]
            n_citas = self.env['sohovet.appointment'].search_count(search_queue)
            if n_citas > 0:
                continue

            # Llamadas
            search_queue = [
                ('partner_id', '=', reminder.partner_id.id),
                ('date', '>=', reminder.date),
            ]
            if not self.exclude_unreachable:
                search_queue.append(('status', '!=', 'unreachable'))
            n_llamadas = self.env['sohovet.vaccine.call_reminder'].search_count(search_queue)
            if n_llamadas > 0:
                continue

            list_of_ids.append(reminder.partner_id.id)
        self.n_items = len(list_of_ids)
        if not self.exclude_unreachable:
            self.batch.write({'calls_remaining': self.n_items})

    @api.multi
    def generate_list(self):
        list_of_ids = []
        for reminder in self.batch.reminder_ids:
            # Siguiente vacuna
            ignore_cliente = False
            for vaccine in reminder.vaccine_ids:
                if vaccine.next_vaccine:
                    ignore_cliente = True

            if ignore_cliente:
                continue

            # Citas
            search_queue = [
                ('partner_id', '=', reminder.partner_id.id),
                ('date_create', '>=', reminder.date)
            ]
            n_citas = self.env['sohovet.appointment'].search_count(search_queue)
            if n_citas > 0:
                continue

            # Llamadas
            search_queue = [
                ('partner_id', '=', reminder.partner_id.id),
                ('date', '>=', reminder.date),
            ]
            if not self.exclude_unreachable:
                search_queue.append(('status', '!=', 'unreachable'))
            n_llamadas = self.env['sohovet.vaccine.call_reminder'].search_count(search_queue)
            if n_llamadas > 0:
                continue

            list_of_ids.append(reminder.partner_id.id)

        action = {
            'name': '%s: Clientes a llamar' % self.batch.name,
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'views': [[False, 'tree'], [False, 'form']],
            'limit': len(list_of_ids),
            'view_type': 'form',
            'target': 'current',
            'domain': [('id', 'in', list_of_ids)]
        }
        return action

