from wtforms import Form, StringField, TextAreaField, PasswordField, validators, FileField, SubmitField
import sqlite3
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import app
from flask_mysqldb import MySQL

class RegisterForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords do not match!')
    ])
    confirm = PasswordField('Confirm Password')


class UploadForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])
    email = StringField('My Email', [validators.Length(min=6, max=50)])
    lectemail = StringField('Lecturer Email', [validators.Length(min=6, max=50)])
    passw = PasswordField('Password', [validators.DataRequired()])
    file = FileField()

class ResetPasswordForm(Form):
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords do not match!')
    ])
    confirm = PasswordField('Confirm Password')
    submit = SubmitField('Reset Password')