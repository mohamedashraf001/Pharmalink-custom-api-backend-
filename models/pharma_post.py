from odoo import models, fields

class PharmaPost(models.Model):
    _name = 'pharma.post'
    _description = 'Pharmacy Post'
    _rec_name = 'medicine_name'

    medicine_name = fields.Char(required=True)
    quantity = fields.Integer(required=True)
    price = fields.Float(required=True)

    status = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('done', 'Done')
    ], default='available')

    pharmacy_id = fields.Many2one('res.partner', string="Pharmacy")

class ApiToken(models.Model):
    _name = 'api.token'
    _description = 'API Token'

    user_id = fields.Many2one('res.users', required=True)
    token = fields.Char(required=True)