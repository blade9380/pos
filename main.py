from flask import Flask, render_template, redirect, url_for, request, abort, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from sqlalchemy import desc
from flask_wtf import FlaskForm, form
from wtforms import StringField, SubmitField
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from wtforms.validators import DataRequired
import requests
from forms import *
from datetime import datetime
from faker import Faker

app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = 'abc'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///items.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user):
    return User.query.get(int(user))


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
    name = db.Column(db.String(100), nullable=False, unique=False)
    purchased_price = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, unique=False)


class MonthlyTotal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Float, nullable=False)
    total_profit = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, unique=True)


class DailyTotal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    daily = db.Column(db.Integer, nullable=False)
    daily_profit = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)


db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_anonymous:
            if current_user.id != 1:
                return abort(403)
            return f(*args, **kwargs)
        return abort(403)

    return decorated_function


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/add', methods=['GET', 'POST'])
@admin_only
def add():
    add_item_form = AddItem()

    if add_item_form.validate_on_submit():
        item = Items.query.filter_by(name=add_item_form.name.data).first()
        if not item:
            new_item = Items(
                name=add_item_form.name.data,
                price=add_item_form.price.data,
                quantity=add_item_form.quantity.data
            )
            db.session.add(new_item)
            db.session.commit()
            return redirect(url_for('add'))
        else:
            return redirect(f'/edit/{item.id}')

    return render_template('add.html', form=add_item_form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # sold_item = User(
    #     name='AMT',
    #     password='AMT'
    # )
    # db.session.add(sold_item)
    # db.session.commit()
    login_form = Login()

    if request.method == 'GET':
        return render_template('login.html', form=login_form)

    if login_form.validate_on_submit():
        email = login_form.name.data
        password = login_form.password.data
        user = User.query.filter_by(name=email).first()
        if not user:
            return redirect(url_for('login'))
        elif password != user.password:
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))


@app.route('/edit_profile', methods=['GET', 'POST'])
@admin_only
def edit_profile():
    edit_user = User.query.get(current_user.id)

    edit_profile_form = EditProfile(
        name=edit_user.name,
        password=edit_user.password
    )

    if request.method == 'GET':
        return render_template('edit_profile.html', form=edit_profile_form)

    if edit_profile_form.validate_on_submit():
        edit_user.name = edit_profile_form.name.data
        edit_user.password = edit_profile_form.password.data
        db.session.commit()
        return redirect(url_for('home'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/show_items', methods=['GET', 'POST'])
@admin_only
def show_items():
    search_form = SearchItem()
    item = Items.query.all()

    if request.method == 'GET':
        return render_template('items.html', items=item, form=search_form)

    if search_form.validate_on_submit():
        searched_item = []
        for i in item:
            if i.name.startswith(search_form.name.data):
                searched_item.append(
                    Items.query.filter_by(name=i.name).first())
        if searched_item:
            return render_template('items.html', items=searched_item, form=search_form)
        else:
            flash("There is no item starts with that name.")
            return redirect(url_for('show_items'))


@app.route('/delete/<int:item_id>')
@admin_only
def delete_item(item_id):
    item_to_delete = Items.query.get(item_id)
    db.session.delete(item_to_delete)
    db.session.commit()

    return redirect(url_for('show_items'))


@app.route('/sold_item_delete/<int:item_id>')
@admin_only
def sold_item_delete(item_id):
    item_to_delete = Sale.query.get(item_id)
    db.session.delete(item_to_delete)
    db.session.commit()

    return redirect(url_for('monthly_total'))


@app.route('/sale/<int:item_id>', methods=['GET', 'POST'])
@admin_only
def sale(item_id):
    sale_form = SaleItem()
    item_to_update = Items.query.get(item_id)

    if request.method == 'GET':
        return render_template('sale.html', form=sale_form, item=item_to_update)

    if sale_form.validate_on_submit():
        price = int(sale_form.price.data)
        quantity = int(sale_form.quantity.data)
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
                purchased_price=updated_item.price,
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
                purchased_price=updated_item.price,
                price=total_sold,
                total=profit,
                quantity=quantity,
                date=datetime.now()
            )
            db.session.add(sold_item)
            db.session.commit()
        else:
            flash("Invalid quantity.")
            return redirect(url_for('sale', item_id=item_id))

        return redirect(url_for('show_items'))


@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@admin_only
def edit(item_id):
    item = Items.query.get(item_id)

    edit_item_form = EditItem(
        name=item.name,
        price=int(item.price),
        quantity=int(item.quantity)
    )

    if request.method == 'GET':
        return render_template('edit.html', form=edit_item_form, item=item)

    if edit_item_form.validate_on_submit():
        item.name = edit_item_form.name.data
        item.price = edit_item_form.price.data
        item.quantity = edit_item_form.quantity.data
        db.session.commit()
        return redirect(url_for('show_items'))


@app.route('/monthly_total')
@admin_only
def monthly_total():
    sold_item = Sale.query.all()
    total = MonthlyTotal.query.all()
    month, year = datetime.now().month, datetime.now().year

    sold_items1 = [i for i in sold_item if i.date.year ==
                   year and i.date.month == month]
    for i in sold_items1:
        print(i.total)
    total1 = [i for i in total if i.date.year ==
              year and i.date.month == month]

    total_money, total_profit = 0, 0

    for i in sold_items1:
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
            i.date = datetime.now()
            db.session.commit()

    new_total = MonthlyTotal.query.all()

    return render_template('total.html', total=new_total)


@app.route('/daily_total/<year_month>')
def daily_total(year_month):
    requested_year, requested_month = int(year_month.split('-')[0]), int(year_month.split('-')[1])
    start_date = datetime.strptime(f'{requested_year}-{requested_month}-1', '%Y-%m-%d')

    if (requested_year % 400 == 0) and (requested_year % 100 == 0) and requested_month == 2:
        end_date = datetime.strptime(f'{requested_year}-{requested_month}-29', '%Y-%m-%d')
    elif (requested_year % 4 == 0) and (requested_year % 100 != 0) and requested_month == 2:
        end_date = datetime.strptime(f'{requested_year}-{requested_month}-29', '%Y-%m-%d')
    elif requested_month in [4, 6, 9, 11]:
        end_date = datetime.strptime(f'{requested_year}-{requested_month}-30', '%Y-%m-%d')
    else:
        end_date = datetime.strptime(f'{requested_year}-{requested_month}-31', '%Y-%m-%d')

    sold_item = Sale.query.all()
    first_daily_total = DailyTotal.query.all()
    today = datetime.now().day
    total_money, total_profit = 0, 0

    sold = [i for i in sold_item if i.date.day == today]
    current_total = [i for i in first_daily_total if i.date.day == today]

    for i in sold:
        total_money += i.price
        total_profit += i.total
    if not current_total:
        add_total = DailyTotal(
            daily=total_money,
            daily_profit=total_profit,
            date=datetime.now()
        )
        db.session.add(add_total)
        db.session.commit()
    else:
        for i in current_total:
            i.daily = total_money
            i.daily_profit = total_profit
            i.date = datetime.now()
            db.session.commit()

    new_total = DailyTotal.query.filter(DailyTotal.date.between(start_date, end_date)).all()

    return render_template('daily_total.html', total=new_total)


@app.route('/sold_items/<date>')
def sold_items(date):
    daily_sold_items = Sale.query.filter_by(date=date).all()
    return render_template('sold_items.html', items=daily_sold_items)


@app.route('/edit_sold_items/<item_id>', methods=['POST', 'GET'])
def edit_sold_items(item_id):
    item = Sale.query.get(item_id)
    edit_sold_item_form = EditSoldItem(
        name=item.name,
        price=int(item.price),
        quantity=int(item.quantity)
    )

    if request.method == 'GET':
        return render_template('edit_sold_items.html', form=edit_sold_item_form, item=item)

    if edit_sold_item_form.validate_on_submit():
        if edit_sold_item_form.confirm.data == 'confirm':
            item.name = edit_sold_item_form.name.data
            item.price = edit_sold_item_form.price.data
            item.quantity = edit_sold_item_form.quantity.data
            item.total = float(edit_sold_item_form.price.data) - item.purchased_price
            db.session.commit()
            return redirect(url_for('sold_items', date=item.date))
        else:
            flash("Please write 'confirm'.")
            return redirect(url_for('edit_sold_items', item_id=item_id))


if __name__ == '__main__':
    app.run(debug=True)
