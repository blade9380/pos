from tokenize import String
from flask import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL


class AddItem(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    quantity = StringField('Quantity', validators=[DataRequired()])
    submit = SubmitField("Submit")


class Login(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class SaleItem(FlaskForm):
    quantity = StringField('Qunatity', validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditItem(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    quantity = StringField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchItem(FlaskForm):
    name = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')
