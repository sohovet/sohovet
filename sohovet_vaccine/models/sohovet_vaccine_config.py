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


class SohovetVaccineConfig(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'sohovet.vaccine.config'

    sms_initial_msg = fields.Char('Cabecera del mensaje')
    sms_end_msg = fields.Char('Final del mensaje')
    sms_batch_size = fields.Integer('Tamaño del lote')

    def _get_parameter(self, key):
        param_obj = self.env['ir.config_parameter']
        rec = param_obj.search([('key', '=', key)])
        return rec or False

    def _write_or_create_param(self, key, value):
        if not value:
            return
        param_obj = self.env['ir.config_parameter']
        rec = self._get_parameter(key)
        if rec:
            rec.value = value
        else:
            param_obj.create({'key': key, 'value': value})

    @api.multi
    def get_default_parameters(self):
        res = {}
        rec = self._get_parameter('sohovet.sms_initial_msg')
        res['sms_initial_msg'] = rec and rec.value or ''
        rec = self._get_parameter('sohovet.sms_end_msg')
        res['sms_end_msg'] = rec and rec.value or ''
        rec = self._get_parameter('sohovet.sms_batch_size')
        res['sms_batch_size'] = rec and int(rec.value) or 0
        return res

    @api.multi
    def set_parameters(self):
        self._write_or_create_param('sohovet.sms_initial_msg', self.sms_initial_msg)
        self._write_or_create_param('sohovet.sms_end_msg', self.sms_end_msg)
        self._write_or_create_param('sohovet.sms_batch_size', self.sms_batch_size)