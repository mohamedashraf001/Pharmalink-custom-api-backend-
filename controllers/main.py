from odoo import http
from odoo.http import request
from odoo.service import common
import jwt
import datetime
import functools

SECRET_KEY = "my_super_secret_key_123"

def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get('Authorization')
        if not access_token:
            return {'success': False, 'message': 'Missing Authorization Header'}

        if access_token.startswith('Bearer '):
            access_token = access_token[7:]

        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=['HS256'])
            # request.update_env ensures that request.env.user is the logged-in user
            request.update_env(user=payload['uid'])
        except jwt.ExpiredSignatureError:
            return {'success': False, 'message': 'Token has expired'}
        except Exception as e:
            return {'success': False, 'message': 'Invalid token'}

        return func(self, *args, **kwargs)
    return wrap

class PharmaAPI(http.Controller):

    @http.route('/api/login', type='json', auth='public', methods=['POST'], csrf=False)
    def login(self, **kwargs):
        data = kwargs.get('params', kwargs)
        db = request.env.cr.dbname
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return {'success': False, 'message': 'Email and password required'}

        try:
            uid = common.exp_login(db, email, password)
            if not uid:
                return {'success': False, 'message': 'Invalid credentials'}

            user = request.env['res.users'].sudo().browse(uid)
            payload = {
                'uid': user.id,
                'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

            return {
                'success': True,
                'token': token,
                'user_id': user.id,
                'name': user.name
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/api/posts', type='json', auth='none', methods=['GET'], csrf=False)
    @validate_token
    def get_posts(self, **kwargs):


        params = request.httprequest.args

        page = int(params.get('page', 1))
        limit = int(params.get('limit', 10))

        status = params.get('status')
        pharmacy_id = params.get('pharmacy_id')
        sort = params.get('sort')  # example: price_desc

        offset = (page - 1) * limit


        domain = []

        if status:
            domain.append(('status', '=', status))

        if pharmacy_id:
            domain.append(('pharmacy_id', '=', int(pharmacy_id)))


        order = 'id desc'

        if sort:
            if sort == 'price_asc':
                order = 'price asc'
            elif sort == 'price_desc':
                order = 'price desc'
            elif sort == 'quantity_asc':
                order = 'quantity asc'
            elif sort == 'quantity_desc':
                order = 'quantity desc'


        posts = request.env['pharma.post'].sudo().search(
            domain,
            offset=offset,
            limit=limit,
            order=order
        )

        total = request.env['pharma.post'].sudo().search_count(domain)

        return {
            'success': True,
            'data': [{
                'id': p.id,
                'medicine_name': p.medicine_name,
                'quantity': p.quantity,
                'price': p.price,
                'status': p.status,
                'pharmacy': p.pharmacy_id.name
            } for p in posts],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total // limit) + (1 if total % limit else 0)
            }
        }

    @http.route('/api/posts/create', type='json', auth='none', methods=['POST'], csrf=False)
    @validate_token
    def create_post(self, **kwargs):
        data = kwargs.get('params', kwargs)
        try:
            new_post = request.env['pharma.post'].sudo().create({
                'medicine_name': data.get('medicine_name'),
                'quantity': data.get('quantity'),
                'price': data.get('price'),
                'pharmacy_id': data.get('pharmacy_id'),
            })
            return {'success': True, 'id': new_post.id}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def role_required(roles):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                user = request.env.user

                if user.role not in roles:
                    return {
                        'success': False,
                        'message': 'Access Denied',
                        'code': 403
                    }

                return func(self, *args, **kwargs)

            return wrapper

        return decorator