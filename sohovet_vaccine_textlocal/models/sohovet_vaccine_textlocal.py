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
import openerp.addons.decimal_precision as dp

from datetime import datetime
import urllib
import urllib2
import json

class sohovet_vaccine_reminder(models.Model):
    _inherit = 'sohovet.vaccine.reminder'

    @api.multi
    def button_send(self):
        self.send()

    @api.one
    def send(self):
        try:
            if self.movilSMS and len(self.movilSMS) == 9 and self.movilSMS.isdigit():
                config = self.env['ir.config_parameter']
                uname = config.get_param('textlocal.user')
                hash_code = config.get_param('textlocal.hash')
                sender = config.get_param('textlocal.sender_name')
                sms_data = {
                    'username': uname,
                    'hash': hash_code,
                    'sender': sender,
                    'numbers': u'34%s' % self.movilSMS,
                    'message': self.text.encode('utf-8'),
                    # 'test': True,
                }

                data = urllib.urlencode(sms_data)
                data = data.encode('utf-8')
                request = urllib2.Request("https://api.txtlocal.com/send/?")
                f = urllib2.urlopen(request, data)
                resp = f.read()
                response = json.loads(resp)
                if response[u'status'] == u'success':
                    self.date = datetime.utcnow()
                    self.state = 'sent'
                    return True
        except Exception:
            return False
        return False

class ReminderSendWizard(models.TransientModel):
    _inherit = 'sohovet.vaccine.reminder.send.wizard'

    confirm = fields.Boolean('Enviar mensajes', default=False)
    total = fields.Float('Precio total', digits=dp.get_precision('Product Price'), readonly=True)
    balance = fields.Integer('Créditos SMS disponibles', default=0, readonly=True)
    has_credits = fields.Boolean('Creditos suficientes', default=False, readonly=True)

    def default_get(self, cr, uid, fields, context=None):
        res = super(ReminderSendWizard, self).default_get(cr, uid, fields, context=context)
        config = self.pool['ir.config_parameter']
        sms_cost = float(config.get_param(cr, uid, 'textlocal.sms_cost'))
        total = res['num_sms'] * sms_cost
        res.update({'total': total})
        try:
            uname = config.get_param(cr, uid, 'textlocal.user')
            hash_code = config.get_param(cr, uid, 'textlocal.hash')
            data = {'username': uname, 'hash': hash_code}
            data = urllib.urlencode(data)
            data = data.encode('utf-8')
            request = urllib2.Request("https://api.txtlocal.com/balance/?")
            f = urllib2.urlopen(request, data)
            resp = f.read()
            response = json.loads(resp)
            res.update({'balance': response['balance']['sms'], 'has_credits': res['num_sms'] <= response['balance']['sms']})
        except Exception:
            pass
        return res

    @api.multi
    def send_all(self):
        if not self.items or len(self.items) == 0:
            return
        n_total = 0
        n_ok = 0
        n_sms = 0
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
            n_total += 1
            item.reminder_id.batch_number = batch_number
            if item.reminder_id.send():
                n_ok += 1
                n_sms += item.reminder_id.num_sms

        self.notify_admins(n_total, n_ok, n_sms)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def notify_admins(self, n_total, n_ok, n_sms):
        config = self.env['ir.config_parameter']

        phones = [phone.strip() for phone in config.get_param('textlocal.admin_phones').split(',')]

        for phone in phones:
            if not len(phone) == 9 or not phone.isdigit():
                continue
            try:
                uname = config.get_param('textlocal.user')
                hash_code = config.get_param('textlocal.hash')
                sender = config.get_param('textlocal.sender_name')
                sms_data = {
                    'username': uname,
                    'hash': hash_code,
                    'sender': sender,
                    'numbers': '34%s' % phone,
                    'message': 'Se han enviado %s notificaciones (%s OK, %s creditos). ' % (n_total, n_ok, n_sms),
                    # 'test': True,
                }

                data = urllib.urlencode(sms_data)
                data = data.encode('utf-8')
                request = urllib2.Request("https://api.txtlocal.com/send/?")
                f = urllib2.urlopen(request, data)
                resp = f.read()
                print resp
            except Exception:
                pass

