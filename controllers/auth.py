from odoo import http
from odoo.http import request
import jwt
import datetime
import functools

SECRET_KEY = "my_super_secret_key_123"


class AuthAPI(http.Controller):

    @http.route('/api/loginn', type='json', auth='public', methods=['POST'], csrf=False)
    def login(self, **kwargs):

        data = kwargs.get('params', kwargs)

        db = "first"
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {
                'success': False,
                'message': 'Email and password are required'
            }

        # 🔥 IMPORTANT: correct Odoo auth method
        from odoo.service import common

        try:
            uid = common.exp_login(db, email, password)

            if not uid:
                return {
                    'success': False,
                    'message': 'Invalid credentials'
                }

            user = request.env['res.users'].sudo().browse(uid)

            payload = {
                'uid': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8)
            }

            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

            return {
                'success': True,
                'token': token,
                'user_id': user.id,
                'name': user.name
            }

        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }