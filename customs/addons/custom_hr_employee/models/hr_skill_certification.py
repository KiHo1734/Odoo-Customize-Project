from odoo import api, fields, models

class SkillCertification(models.Model):
    _inherit = 'hr.employee.skill'

    certification_file = fields.Binary(string="Certificate File")
    certification_filename = fields.Char(string="Filename")
