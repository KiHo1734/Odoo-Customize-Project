from odoo import http
from odoo.http import request

class ShopfloorController(http.Controller):

    @http.route('/shopfloor/workorders', type='json', auth='user')
    def get_workorders(self):
        workorders = request.env['mrp.workorder'].search([
            ('state', 'in', ['ready', 'progress'])
        ])
        return [{
            'id': w.id,
            'name': w.name,
            'product': w.product_id.display_name,
            'qty': w.qty_production,
            'state': w.state,
        } for w in workorders]

    @http.route('/shopfloor/start', type='json', auth='user')
    def start_work(self, workorder_id):
        wo = request.env['mrp.workorder'].browse(workorder_id)
        wo.button_start()
        return {'success': True}
