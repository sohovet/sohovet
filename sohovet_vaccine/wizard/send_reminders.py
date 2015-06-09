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
import base64
import StringIO
import xlsxwriter

class ReminderSendWizard(models.TransientModel):
    _name = 'sohovet.vaccine.reminder.send.wizard'
    _description = 'Enviar recordatorios'

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(ReminderSendWizard, self).default_get(cr, uid, fields, context=context)
        config = self.pool.get('ir.config_parameter')
        batch_size = config.get_param(cr, uid, 'sohovet.sms_batch_size')
        batch_size = batch_size and batch_size.isdigit() and int(batch_size) or 0
        if 'send_all' in context:
            reminder_ids = self.pool.get('sohovet.vaccine.reminder').search(cr, uid, [('state', 'in', ['draft', 'incomplete'])])
        elif 'send_batch' in context:
            reminder_ids = self.pool.get('sohovet.vaccine.reminder').search(cr, uid, [('state', 'in', ['draft'])])[:batch_size]
        elif 'send_selected_batch' in context:
            reminder_ids = context['active_ids'][:batch_size]
        elif 'send_all_selected' in context:
            reminder_ids = context['active_ids']
        else:
            raise ValidationError('Error en el contexto')
        reminders = self.pool.get('sohovet.vaccine.reminder').browse(cr, uid, reminder_ids, context=context)
        items = []
        num_sms = 0
        for reminder in reminders:
            if reminder.state in ['sent', 'cancelled']:
                continue
            item_data = {
                'reminder_id': reminder.id,
            }
            items.append(item_data)
            if reminder.state == 'draft':
                num_sms += reminder.num_sms
        bin_file = self.get_bin(reminders)
        res.update({'items': items, 'num_sms': num_sms, 'num_reminders': len(items), 'bin_file': bin_file,
                    'filename': 'Recordatorios.xlsx'})
        return res

    items = fields.One2many('sohovet.vaccine.reminder.send.item', 'wizard_id', string='Mensajes')
    num_reminders = fields.Integer('Clientes a notificar')
    # num_vaccines = fields.Integer('Número de vacunas')
    num_sms = fields.Integer('Créditos SMS')
    bin_file = fields.Binary('Fichero XLSX')
    filename = fields.Char('Nombre del fichero')


    def get_bin(self, reminders):
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('SMS')

        format_header = workbook.add_format({'bg_color': 'black', 'font_color': 'white', 'bold': True})
        header = [u'Propietario', u'SMS', u'#', u'C/F', u'Animal', u'Tratamiento', u'Última', u'Siguiente']
        widths = [32, 110, 4, 4, 9, 15, 9, 9]
        for i in range(len(header)):
            worksheet.write(0, i, header[i], format_header)
            worksheet.set_column(i, i, widths[i])

        n, i = 0, 1
        format1 = workbook.add_format({'num_format': 49})
        format1_merged = workbook.add_format({'num_format': 49, 'align': 'top', 'text_wrap': True})
        format2 = workbook.add_format({'num_format': 49, 'bg_color': '#DDDDDD'})
        format2_merged = workbook.add_format({'num_format': 49, 'bg_color': '#DDDDDD', 'align': 'top', 'text_wrap': True})

        reminders = sorted(reminders, key=lambda x: x.partner_id.name)
        reminders = sorted(reminders, key=lambda x: x.state, reverse=True)
        for reminder in reminders:
            first_line = True
            for vaccine in reminder.vaccine_ids:
                if first_line:
                    first_line = False
                    if reminder.partner_id.mobile and len(reminder.partner_id.mobile) == 9 \
                            and reminder.partner_id.mobile.isdigit():
                        worksheet.write(i, 0, reminder.partner_id.name, format1 if n % 2 else format2)
                    else:
                        worksheet.write(i, 0, u'[ ! ] %s' % reminder.partner_id.name, format1 if n % 2 else format2)
                    worksheet.write(i, 2, reminder.num_sms, format1 if n % 2 else format2)
                    if len(reminder.vaccine_ids) > 1:
                        worksheet.merge_range('B%d:B%d' % (i+1, i+len(reminder.vaccine_ids)),
                                              reminder.text, format1_merged if n % 2 else format2_merged)
                    else:
                        worksheet.write(i, 1, reminder.text, format1 if n % 2 else format2)
                else:
                    worksheet.write(i, 0, '', format1 if n % 2 else format2)
                    worksheet.write(i, 2, '', format1 if n % 2 else format2)
                worksheet.write(i, 3, vaccine.animal_id.type_id.name, format1 if n % 2 else format2)
                worksheet.write(i, 4, vaccine.animal_id.name, format1 if n % 2 else format2)
                worksheet.write(i, 5, vaccine.type_id.name, format1 if n % 2 else format2)
                worksheet.write(i, 6, '%s-%s' % (vaccine.date[5:7], vaccine.date[0:4]), format1 if n % 2 else format2)
                worksheet.write(i, 7, '%s-%s' % (vaccine.date_next_computed[5:7], vaccine.date_next_computed[0:4]), format1 if n % 2 else format2)
                i += 1
            n += 1
        workbook.close()
        bin_file = base64.encodestring(output.getvalue())
        return bin_file

    @api.multi
    def send_all(self):
        if not self.items or len(self.items) == 0:
            return
        batch_number = self.env['ir.sequence'].next_by_code('reminder.batch.sequence')
        batch_type = self.items[0].reminder_id.type

        if not all([item.reminder_id.type == batch_type for item in self.items]):
            batch_type = 'mixed'

        batch_data = {
            'name': batch_number,
            'type': batch_type,
            'reminder_ids': [item.reminder_id.id for item in self.items],
            'date': fields.Datetime.now(),
        }
        self.env['sohovet.vaccine.reminder.batch'].create(batch_data)

        for item in self.items:
            item.reminder_id.send()
            item.reminder_id.batch_number = batch_number

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

class ReminderSendItem(models.TransientModel):
    _name = 'sohovet.vaccine.reminder.send.item'
    _description = 'Mensaje SMS'

    wizard_id = fields.Many2one('sohovet.vaccine.reminder.send.wizard', 'Wizard ID', required=True, ondelete='cascade')
    reminder_id = fields.Many2one('sohovet.vaccine.reminder', 'Recordatorio', required=True, ondelete='cascade')

