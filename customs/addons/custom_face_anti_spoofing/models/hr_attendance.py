from odoo import models, fields

class HRAttendance(models.Model):
    _inherit = "hr.attendance"

    def _update_overtime(self, attendances_dates=None):
        # ข้าม ไม่คำนวณ OT
        return


    missed_checkout = fields.Boolean(
        string="Missed Checkout",
        default=False,
        help="Automatically marked when employee forgot to check out."
    )
