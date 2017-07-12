from flask_wtf import Form
from wtforms import StringField, PasswordField,TextField
from wtforms.validators import DataRequired

class Login(Form):
    username = StringField('username',validators=[DataRequired()])
    password = PasswordField('passsword',validators=[DataRequired()])
class Register(Form):
    username = StringField('username',validators=[DataRequired()])
    password = PasswordField('passsword',validators=[DataRequired()])

class Broadcast(Form):
    broadcast_text = StringField('broadcast_text',validators=[DataRequired()])
   
