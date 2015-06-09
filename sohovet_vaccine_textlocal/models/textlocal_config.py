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
from openerp import api, fields, models


class TextLocalConfig(models.TransientModel):
    _inherit = 'sohovet.vaccine.config'

    textlocal_sender_name = fields.Char('Remitente', size=11)
    textlocal_user = fields.Char('Usuario')
    textlocal_hash = fields.Char('Hash')
    textlocal_sms_cost = fields.Float('Precio del SMS', digits=(10, 4))
    textlocal_admin_phones = fields.Char('Móviles de los administradores')


    @api.multi
    def get_default_parameters(self):
        res = super(TextLocalConfig, self).get_default_parameters()
        rec = self._get_parameter('textlocal.sender_name')
        res['textlocal_sender_name'] = rec and rec.value or ''
        rec = self._get_parameter('textlocal.user')
        res['textlocal_user'] = rec and rec.value or ''
        rec = self._get_parameter('textlocal.hash')
        res['textlocal_hash'] = rec and rec.value or ''
        rec = self._get_parameter('textlocal.sms_cost')
        res['textlocal_sms_cost'] = rec and float(rec.value) or 0
        rec = self._get_parameter('textlocal.admin_phones')
        res['textlocal_admin_phones'] = rec and rec.value or ''
        return res

    @api.multi
    def set_parameters(self):
        super(TextLocalConfig, self).set_parameters()
        self._write_or_create_param('textlocal.sender_name',
                                    self.textlocal_sender_name)
        self._write_or_create_param('textlocal.user',
                                    self.textlocal_user)
        self._write_or_create_param('textlocal.hash',
                                    self.textlocal_hash)
        self._write_or_create_param('textlocal.sms_cost',
                                    self.textlocal_sms_cost)
        self._write_or_create_param('textlocal.admin_phones',
                                    self.textlocal_admin_phones)