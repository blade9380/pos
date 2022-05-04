from logging import PlaceHolder
from flask import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL


class AddItem(FlaskForm):
    name = StringField("Name", validators=[DataRequired()], render_kw={'placeholder': 'Item Name', 'class': 'input'})
    price = StringField('Price', validators=[DataRequired()], render_kw={'placeholder': "Item Price"})
    quantity = StringField('Quantity', validators=[DataRequired()], render_kw={'placeholder': 'Item quantity'})
    submit = SubmitField("Submit")


class Login(FlaskForm):
    name = StringField("Name", validators=[DataRequired()], render_kw={'placeholder': 'Username'})
    password = PasswordField("Password", validators=[DataRequired()], render_kw={'placeholder': 'password'})
    submit = SubmitField("Login")


class SaleItem(FlaskForm):
    price = StringField('Price', validators=[DataRequired()])
    quantity = StringField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditItem(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    quantity = StringField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SearchItem(FlaskForm):
    name = StringField('Search', validators=[DataRequired()], render_kw={'placeholder': 'Search Item'})
    submit = SubmitField('Search')


class EditProfile(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    password = StringField('Password', validators=[DataRequired()])
    submit = SubmitField('Submit')