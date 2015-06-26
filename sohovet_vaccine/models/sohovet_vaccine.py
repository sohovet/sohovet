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
import calendar
from datetime import datetime
from string import Template
import xlsxwriter


def join_str(str_list, mid_separator=u', ', final_separator=u' y '):
    if not str_list:
        return u''
    elif len(str_list) == 1:
        return str_list[0]
    else:
        res = mid_separator.join(str_list[:-1])
        res += u'%s%s' % (final_separator, str_list[len(str_list) - 1])
        return res

class sohovet_vaccine_type(models.Model):
    _name = 'sohovet.vaccine.type'
    _description = 'Vaccine types'

    name = fields.Char('Tipo', required=True)

class sohovet_vaccine_rule(models.Model):
    _name = 'sohovet.vaccine.rule'
    _description = 'Vaccination rules'

    sequence = fields.Integer('Sequence')
    animal_type_id = fields.Many2one('sohovet.animal.type', string='Tipo de animal', required=True)
    type_id = fields.Many2one('sohovet.vaccine.type', string='Tipo de vacuna', required=True)
    next_type_id = fields.Many2one('sohovet.vaccine.type', string='Tipo de la siguiente vacuna', required=True)
    periodicity = fields.Integer('Periodicidad (en meses)', default=12, required=True)

    @api.multi
    def name_get(self):
        result = []
        for rule in self:
            result.append((rule.id, "[%s] %s -> %s" % (rule.animal_type_id.code, rule.type_id.name, rule.next_type_id.name)))
        return result

class sohovet_vaccine(models.Model):
    _name = 'sohovet.vaccine'
    _description = 'Vaccine'
    _order = 'date'

    type_id = fields.Many2one('sohovet.vaccine.type', 'Tipo', required=True)
    animal_id = fields.Many2one('sohovet.animal', 'Animal', required=True)
    date = fields.Date('Fecha', required=True)
    extern = fields.Boolean('Externa')
    reminder_ids = fields.Many2many('sohovet.vaccine.reminder', 'sohovet_vaccine_reminder_vaccines', 'vaccine_id',
                                    'reminder_id', string="Recordatorios", readonly=True, domain=[('state', '=', 'sent')])
    num_sent_reminders = fields.Integer('Recordatorios enviados', compute='_get_num_sent_reminders', store=True)
    last_reminder_date = fields.Date('Fecha del último recordatorio', compute='_get_num_sent_reminders', store=True)

    other_vaccines = fields.One2many('sohovet.vaccine', related='animal_id.vaccines', readonly=True)

    partner_active = fields.Boolean('Propietario activo', related='animal_id.partner_active', readonly=True)
    animal_active = fields.Boolean('Activo', related='animal_id.partner_id.active', readonly=True)
    animal_alive = fields.Boolean('Vivo', related='animal_id.alive', readonly=True)
    animal_type_id = fields.Many2one('sohovet.animal.type', string='Tipo animal', related='animal_id.type_id', readonly=True)

    next_vaccine_rule = fields.Many2one('sohovet.vaccine.rule', string='Regla para siguiente vacunación', readonly=True)
    next_vaccine = fields.Many2one('sohovet.vaccine', string='Siguiente vacuna', readonly=True, store=True)
    date_next = fields.Date('Fecha real de la siguiente vacunación', related='next_vaccine.date', readonly=True)
    next_type_id = fields.Many2one('sohovet.vaccine.type', string='Tipo de la siguiente vacuna', readonly=True,
                                   compute='_get_next_vaccine_type_and_date', store=True)
    date_next_computed = fields.Date('Fecha calculada de la siguiente vacunación',
                                     compute='_get_next_vaccine_type_and_date', store=True)
    partner_id = fields.Many2one('res.partner', 'Propietario', related='animal_id.partner_id', readonly=True,
                                 store=True)
    specie_id = fields.Many2one('sohovet.animal.specie', 'Especie', related='animal_id.specie_id', readonly=True,
                                store=True)

    @api.one
    @api.depends('type_id', 'animal_type_id', 'date')
    def _get_next_vaccine_type_and_date(self):
        rules = self.env['sohovet.vaccine.rule'].search([('type_id', '=', self.type_id.id),
                                                         ('animal_type_id', '=', self.animal_type_id.id)])
        if rules:
            self.next_vaccine_rule = rules[0]
            self.next_type_id = self.next_vaccine_rule.next_type_id
            if self.date:
                date = datetime.strptime(self.date, '%Y-%m-%d')
                month = date.month - 1 + self.next_vaccine_rule.periodicity
                year = date.year + month / 12
                month = month % 12 + 1
                day = min(date.day, calendar.monthrange(year, month)[1])
                self.date_next_computed = datetime(year, month, day)
        else:
            self.next_type_id = False
            self.date_next_computed = False

    @api.one
    @api.depends('reminder_ids', 'reminder_ids.state')
    def _get_num_sent_reminders(self):
        self.num_sent_reminders = 0
        self.last_reminder_date = False
        for reminder in self.reminder_ids:
            if reminder.state == 'sent':
                self.num_sent_reminders += 1
                if not self.last_reminder_date or reminder.date > self.last_reminder_date:
                    self.last_reminder_date = reminder.date

    @api.multi
    def name_get(self):
        result = []
        for vaccine in self:
            result.append((vaccine.id, "%s: %s" % (vaccine.type_id.name, vaccine.animal_id.name)))
        return result

    @api.model
    def create(self, vals):
        res = super(sohovet_vaccine, self).create(vals)

        search_data = [
            ('id', '!=', res.id),
            ('animal_id', '=', res.animal_id.id),
            ('next_vaccine', '=', False),
            ('next_type_id', '=', res.type_id.id),
            ('date', '<=', res.date),

        ]
        vaccines = self.search(search_data)

        # vaccines = res.other_vaccines.filtered(lambda record: not record.next_vaccine and
        #                                                       record.id != res.id and
        #                                                       record.animal_id == res.animal_id and
        #                                                       record.next_type_id == res.type_id and
        #                                                       record.date <= res.date)

        for vaccine in vaccines:
            vaccine.next_vaccine = res

        search_data = [
            ('id', '!=', res.id),
            ('type_id', '=', res.next_type_id.id),
            ('date', '>', res.date),

        ]
        filtered = self.search(search_data, order='date')

        # filtered = self.other_vaccines.filtered(lambda record: record.type_id == res.next_type_id and
        #                                                        record.date > res.date)

        if filtered:
            res.next_vaccine = filtered[0]
        return res

class sohovet_vaccine_reminder(models.Model):
    _name = 'sohovet.vaccine.reminder'
    _description = 'Vaccine reminder'
    _rec_name = 'partner_id'
    _inherit = ['ir.needaction_mixin']
    _order = 'state ASC, date DESC, id DESC'

    type = fields.Selection([('first', 'Inicial'), ('other', 'Repesca')], 'Tipo de recordatorio', required=True)
    partner_id = fields.Many2one('res.partner', 'Propietario', required=True)
    movilSMS = fields.Char('Movil SMS', related='partner_id.mobile', readonly=True)
    vaccine_ids = fields.Many2many('sohovet.vaccine', 'sohovet_vaccine_reminder_vaccines', 'reminder_id', 'vaccine_id',
                                   string="Vacunas")
    state = fields.Selection(selection=[('draft', 'Borrador'), ('sent', 'Enviado'), ('cancel', 'Cancelado'),
                                        ('incomplete', 'Incompleto')], string='Estado', default='draft')
    date = fields.Datetime('Fecha de envío')
    text = fields.Text('Mensaje')
    num_characters = fields.Integer('Num. de caracteres', compute='get_num_characters', size='765')
    num_sms = fields.Integer('Num. de SMS', compute='get_num_characters', store=True)
    batch_number = fields.Char('Número de lote', readonly=True)

    n_animals = fields.Integer('Número de animales', compute='on_set_vaccine_ids', store=True)
    n_vaccines = fields.Integer('Número de vacunas', compute='on_set_vaccine_ids', store=True)
    all_equal_type = fields.Boolean('Todas iguales', compute='on_set_vaccine_ids', store=True)

    @api.model
    def _needaction_domain_get(self):
        return [('state', '=', 'draft')]

    @api.one
    @api.depends('date')
    def _is_sent(self):
        self.sent = self.date

    @api.one
    @api.depends('text')
    def get_num_characters(self):
        sms_limit = [160, 306, 459, 612, 765]
        self.num_characters = self.text and len(self.text) or 0
        self.num_sms = 1
        while self.num_characters > sms_limit[self.num_sms - 1]:
            self.num_sms += 1
        return True

    @api.one
    def send(self):
        self.state = 'sent'
        self.date = datetime.utcnow()

    # @api.one
    # @api.depends('vaccine_ids')
    # def _get_num_vaccines(self):
    #     self.num_vaccines = self.vaccine_ids and len(self.vaccine_ids) or 0

    @api.one
    @api.depends('vaccine_ids')
    def on_set_vaccine_ids(self):
        self.all_equal_type = not self.vaccine_ids or \
                          all(vaccine.type_id == self.vaccine_ids[0].type_id for vaccine in self.vaccine_ids)
        self.n_vaccines = len(self.vaccine_ids)
        self.n_animals = len(set([vaccine.animal_id for vaccine in self.vaccine_ids]))
        return True

    @api.one
    def generate_default_msg(self):
        vaccines_map = {}
        for vaccine in self.vaccine_ids:
            if vaccine.animal_id in vaccines_map:
                vaccines_map[vaccine.animal_id].append(vaccine)
            else:
                vaccines_map[vaccine.animal_id] = [vaccine]

        if self.partner_id.firstname:
            nombre = self.partner_id.firstname.title().strip()
        else:
            nombre = self.partner_id.name

        config = self.env['ir.config_parameter']
        init_msg = config.get_param('sohovet.sms_initial_msg')
        end_msg = config.get_param('sohovet.sms_end_msg')
        template_init = Template(init_msg)

        self.text = u'%s ' % template_init.safe_substitute(nombre=nombre) if init_msg else u''
        if len(vaccines_map) == 1:
            animal = vaccines_map.keys()[0]
            self.text += u'%s tiene pendiente %s.'\
                         % (animal.name.strip(), self.get_message(vaccines_map[animal]))
        elif all([set([vaccine.type_id for vaccine in vaccines_map.values()[0]]) ==
                          set([vaccine.type_id for vaccine in vaccines]) for vaccines in vaccines_map.values()]):
            str_list = [animal.name for animal in vaccines_map]
            self.text += u'Hay que administrarle a %s %s.' % \
                         (join_str(str_list), self.get_message(vaccines_map.values()[0]))
        else:
            str_list = [u'a %s (%s)' % (animal.name.strip(), self.get_short_message(vaccines_map[animal]))
                        for animal in vaccines_map]
            self.text += u'Hay que administrale tratamientos %s.' % join_str(str_list)

        self.text += u' %s' % end_msg

    def get_message(self, vaccines):
        str_list = []
        for vaccine in vaccines:
            search_data = [
                ('animal_type_id', '=', vaccine.animal_id.type_id.id),
                ('type_id', '=', vaccine.type_id.id),
            ]
            messages = self.env['sohovet.vaccine.reminder.message'].search(search_data)
            month = datetime.utcnow().month
            for message in messages:
                    if message.init_month <= month <= message.end_month or \
                            message.end_month < message.init_month <= month <= 12 or \
                            1 <= month <= message.end_month < message.init_month:
                        str_list.append(message.message)
        return join_str(str_list)

    def get_short_message(self, vaccines):
        str_list = []
        for vaccine in vaccines:
            search_data = [
                ('animal_type_id', '=', vaccine.animal_id.type_id.id),
                ('type_id', '=', vaccine.type_id.id),
            ]
            messages = self.env['sohovet.vaccine.reminder.message'].search(search_data)
            month = datetime.utcnow().month
            for message in messages:
                    if message.init_month <= month <= message.end_month or \
                            message.end_month < message.init_month <= month <= 12 or \
                            1 <= month <= message.end_month < message.init_month:
                        str_list.append(message.short_message)
        return join_str(str_list)

    @api.model
    def create(self, vals):
        res = super(sohovet_vaccine_reminder, self).create(vals)
        if not res.text:
            res.generate_default_msg()
        if not res.partner_id.mobile:
            res.state = 'incomplete'
        return res

class sohovet_vaccine_reminder_batch(models.Model):
    _name = 'sohovet.vaccine.reminder.batch'
    _description = 'Vaccine reminder batch'

    name = fields.Char('Nombre', readonly=True, required=True)
    type = fields.Selection([('first', 'Inicial'), ('other', 'Repesca'), ('mixed', 'Varios')], 'Tipo de recordatorio',
                            readonly=True, required=True)
    reminder_ids = fields.Many2many('sohovet.vaccine.reminder', 'sohovet_vaccine_reminder_batch_rel', 'vaccine_id',
                                    'reminder_id', string="Recordatorios", readonly=True, required=True)
    date = fields.Datetime('Fecha de envio', readonly=True, required=True)

    @api.multi
    def name_get(self):
        result = []
        for batch in self:
            date = fields.Datetime.from_string(batch.date)
            result.append((batch.id, "%s (%s)" % (date.strftime("%d-%m-%Y"), batch.name)))
        return result


class sohovet_vaccine_reminder_message(models.Model):
    _name = 'sohovet.vaccine.reminder.message'
    _description = 'Vaccine reminder message'

    type_id = fields.Many2one('sohovet.vaccine.type', string='Tipo de vacuna', required=True)
    animal_type_id = fields.Many2one('sohovet.animal.type', string='Tipo de animal', required=True)
    init_month = fields.Integer('Mes inicial', default=1)
    end_month = fields.Integer('Mes final', default=12)
    message = fields.Char('Mensaje')
    short_message = fields.Char('Mensaje corto')

class sohovet_animal(models.Model):
    _inherit = 'sohovet.animal'

    vaccines = fields.One2many('sohovet.vaccine', 'animal_id', string='Vacunas')