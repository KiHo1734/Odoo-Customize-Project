from odoo import http
from odoo.http import request
import json

class FaceScanController(http.Controller):
    @http.route('/hr_attendance/scan_face', type='http', auth='public', csrf=False, methods=['POST'])
    def scan_face(self, **post):
        try:
            data = json.loads(request.httprequest.data)
            image_base64 = data.get('image_base64', '')
            result = request.env['face.scanner'].sudo().find_employee_by_image(image_base64)
            return request.make_response(json.dumps({'success': True, 'employees': result}),
                                         [('Content-Type', 'application/json')])
        except Exception as e:
            return request.make_response(json.dumps({'success': False, 'employees': [str(e)]}),
                                         [('Content-Type', 'application/json')])
