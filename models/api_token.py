from odoo import models, fields
import uuid


class ApiToken(models.Model):
    _name = 'api.token'
    _description = 'API Token'

    user_id = fields.Many2one('res.users', required=True)
    token = fields.Char(required=True, default=lambda self: str(uuid.uuid4()))