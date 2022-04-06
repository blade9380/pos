from re import S, U
from flask import Flask, render_template, redirect, url_for, request, abort, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from sqlalchemy import desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from wtforms.validators import DataRequired
import requests
from forms import *
from datetime import datetime

app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = 'abc'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///items.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


class Items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)


class MonthlyTotal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Float, nullable=False)
    total_profit = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)


db.create_all()


@login_manager.user_loader
def load_user(user):
    return User.get(user)


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.name != 'AMT':
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddItem()
    if form.validate_on_submit():
        item = Items.query.filter_by(name=form.name.data).first()
        if not item:
            new_item = Items(
                name=form.name.data,
                price=form.price.data,
                quantity=form.quantity.data
            )
            db.session.add(new_item)
            db.session.commit()
            return redirect(url_for('add'))
        else:
            return redirect(f'/edit/{item.id}')
    return render_template('add.html', form=form)


@ app.route('/login')
def login():
    form = Login()
    if form.validate_on_submit():
        email = form.name.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            return redirect(url_for('login'))
        elif password != user.password:
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html', form=form)


@ app.route('/show_items', methods=['GET', 'POST'])
def show_items():
    form = SearchItem()
    item = Items.query.all()
    if request.method == 'GET':
        return render_template('items.html', items=item, form=form)
    if form.validate_on_submit():
        searched_item = []
        for i in item:
            if i.name.startswith(form.name.data):
                searched_item.append(
                    Items.query.filter_by(name=i.name).first())
        if searched_item:
            return render_template('items.html', items=searched_item, form=form)
        else:
            flash("There is no item starts with that name.")
            return redirect(url_for('show_items'))


@ app.route('/delete/<int:item_id>')
def delete_item(item_id):
    item_to_delete = Items.query.get(item_id)
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for('show_items'))


@ app.route('/sale/<int:item_id>', methods=['GET', 'POST'])
def sale(item_id):
    form = SaleItem()
    item_to_update = Items.query.get(item_id)
    if request.method == 'GET':
        return render_template('sale.html', form=form, item=item_to_update)
    if form.validate_on_submit():
        price = int(form.price.data)
        quantity = int(form.quantity.data)
        updated_item = Items.query.get(item_id)
        total_sold = price * quantity
        profit = total_sold - (updated_item.price * quantity)
        if updated_item.quantity - quantity > 0:
            updated_item.quantity = updated_item.quantity - quantity
            db.session.commit()
            sold_item = Sale(
                name=item_to_update.name,
                price=total_sold,
                total=profit,
                quantity=quantity,
                date=datetime.now()
            )
            db.session.add(sold_item)
            db.session.commit()
        elif updated_item.quantity - quantity == 0:
            db.session.delete(item_to_update)
            db.session.commit()
            sold_item = Sale(
                name=item_to_update.name,
                price=total_sold,
                total=profit,
                quantity=quantity,
                date=datetime.now()
            )
            db.session.add(sold_item)
            db.session.commit()
        else:
            flash("Invaild quantity.")
            return redirect(url_for('sale', item_id=item_id))
        return redirect(url_for('show_items'))


@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit(item_id):
    item = Items.query.get(item_id)
    form = EditItem(
        name=item.name,
        price=int(item.price),
        quantity=int(item.quantity)
    )
    if request.method == 'GET':
        return render_template('edit.html', form=form, item=item)
    if form.validate_on_submit():
        item.name = form.name.data
        item.price = form.price.data
        item.quantity = form.quantity.data
        db.session.commit()
        return redirect(url_for('show_items'))


@app.route('/total')
def total():
    sold_item = Sale.query.all()
    total = MonthlyTotal.query.all()
    month, year = datetime.now().month, datetime.now().year
    sold_items = [i for i in sold_item if i.date.year ==
                  year and i.date.month == month]
    total1 = [i for i in total if i.date.year ==
              year and i.date.month == month]
    total_money, total_profit = 0, 0
    for i in sold_items:
        total_money += i.price
        total_profit += i.total
    if not total1:
        add_total = MonthlyTotal(
            total=total_money,
            total_profit=total_profit,
            date=datetime.now()
        )
        db.session.add(add_total)
        db.session.commit()
    else:
        for i in total:
            i.total = total_money
            i.total_profit = total_profit
            db.session.commit()
    new_total = MonthlyTotal.query.all()
    return render_template('total.html', total=new_total)


if __name__ == '__main__':
    app.run(debug=True)
