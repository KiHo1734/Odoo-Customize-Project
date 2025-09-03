from odoo import models, fields

class HrAttendanceSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    work_start = fields.Float(string="Work Start (hour)", default=8.0)
    work_end = fields.Float(string="Work End (hour)", default=17.0)

    def get_values(self):
        res = super(HrAttendanceSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            work_start=float(params.get_param('hr_attendance.work_start', 8.0)),
            work_end=float(params.get_param('hr_attendance.work_end', 17.0)),
        )
        return res

    def set_values(self):
        super(HrAttendanceSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('hr_attendance.work_start', self.work_start)
        params.set_param('hr_attendance.work_end', self.work_end)
        
