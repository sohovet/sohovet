# -*- encoding: utf-8 -*-
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
from openerp import fields, models, api

from openerp.exceptions import ValidationError
from openerp.service import db

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3ResponseError

import tempfile
import base64
import socket

class sohovet_backup(models.Model):
    _name = 'sohovet.backup'
    _description = 'Backup'

    name = fields.Char('Name')
    type = fields.Selection([('auto', u'Automático'), ('manual', u'Manual')], 'Tipo')

    @api.multi
    def get_aws_obj(self, name):
        config = self.env['ir.config_parameter']
        a_key = config.get_param('sohovet.aws_a_key')
        s_key = config.get_param('sohovet.aws_s_key')
        bucket = config.get_param('sohovet.aws_backup_bucket')

        if not (a_key and s_key and bucket):
            raise ValidationError(u'La cuenta de AWS no está configurada')
        conn = S3Connection(a_key, s_key)
        bucket_obj = conn.lookup(bucket)
        k = Key(bucket_obj)
        k.key = name
        return k

    @api.multi
    def download(self):
        try:
            k = self.get_aws_obj(self.name)
            backup = k.get_contents_as_string()
            bin_file = base64.encodestring(backup)

            wizard = self.env['sohovet.backup.export.wizard'].create({'data': bin_file, 'name': self.name})
            return wizard.open()
        except S3ResponseError:
            raise ValidationError('No se puede conectar a AWS o el fichero no existe')

    @api.model
    def create_backup(self, type='auto'):
        print 'Call to create_backup()'

        config = self.env['ir.config_parameter']
        hosts_str = config.get_param('sohovet.aws_hostname_list')
        hosts = hosts_str and hosts_str.split(',') or False
        if hosts and not socket.gethostname() in [host.strip() for host in hosts]:
            return

        name = ('%s_%s.zip' % (self._cr.dbname, fields.Datetime.now())).replace(' ', '_').replace(':', '-')

        self.clean_db()

        backup = tempfile.TemporaryFile()
        db.dump_db(self._cr.dbname, backup)
        backup.seek(0)

        k = self.get_aws_obj(name)
        k.set_contents_from_file(backup)
        backup.close()

        self.create({'name': name, 'type': type})

    @api.model
    def clean_db(self):
        for wizard in self.env['sohovet.backup.export.wizard'].search([]):
            wizard.unlink()

class sohovet_backup_config(models.TransientModel):
    _inherit = 'res.config.settings'
    _name = 'sohovet.backup.config'

    a_key = fields.Char('Clave de acceso de AWS')
    s_key = fields.Char('Clave secreta de AWS')
    backup_bucket = fields.Char('Nombre del bucket')
    hostname_list = fields.Char('Lista de hostnames')

    active = fields.Boolean('Realizar copias de seguridad automáticas')
    interval_number = fields.Integer('Repetir cada')
    nextcall = fields.Datetime('Fecha de la siguiente copia')

    def _get_parameter(self, key):
        cron = self.env.ref('sohovet_backup_S3.sohovet_backup_cron')
        if key == 'active':
            rec = cron.active
        elif key == 'interval_number':
            rec = cron.interval_number
        elif key == 'nextcall':
            rec = cron.nextcall
        else:
            param_obj = self.env['ir.config_parameter']
            rec = param_obj.search([('key', '=', key)])
        return rec or False

    def _write_or_create_param(self, key, value):
        if not value:
            return
        cron = self.env.ref('sohovet_backup_S3.sohovet_backup_cron')
        if key == 'active':
            cron.active = value
        elif key == 'interval_number':
            cron.interval_number = value
        elif key == 'nextcall':
            cron.nextcall = value
        else:
            param_obj = self.env['ir.config_parameter']
            rec = self._get_parameter(key)
            if rec:
                rec.value = value
            else:
                param_obj.create({'key': key, 'value': value})

    @api.multi
    def get_default_parameters(self):
        res = {}
        rec = self._get_parameter('sohovet.aws_a_key')
        res['a_key'] = rec and rec.value or ''
        rec = self._get_parameter('sohovet.aws_s_key')
        res['s_key'] = rec and rec.value or ''
        rec = self._get_parameter('sohovet.aws_backup_bucket')
        res['backup_bucket'] = rec and rec.value or ''
        rec = self._get_parameter('sohovet.aws_hostname_list')
        res['hostname_list'] = rec and rec.value or ''

        cron = self.env.ref('sohovet_backup_S3.sohovet_backup_cron')
        res['active'] = cron.active
        res['interval_number'] = cron.interval_number
        res['nextcall'] = cron.nextcall
        return res

    @api.multi
    def set_parameters(self):
        self._write_or_create_param('sohovet.aws_a_key', self.a_key)
        self._write_or_create_param('sohovet.aws_s_key', self.s_key)
        self._write_or_create_param('sohovet.aws_backup_bucket', self.backup_bucket)
        self._write_or_create_param('sohovet.aws_hostname_list', self.hostname_list)

        cron = self.env.ref('sohovet_backup_S3.sohovet_backup_cron')
        cron.active = self.active
        cron.interval_number = self.interval_number
        cron.nextcall = self.nextcall

    @api.multi
    def manual_backup(self):
        self.env['sohovet.backup'].create_backup(type='manual')