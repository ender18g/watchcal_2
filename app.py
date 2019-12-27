from flask import Flask, flash, render_template, render_template_string, request, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from random import randint, choice
import os
from config import Config
from datetime import date, timedelta
from calendar import monthrange
from flask_migrate import Migrate
import holidays
import json
import pickle
from flask_login import LoginManager, logout_user, login_user, current_user, login_required, UserMixin
from flask_openid import OpenID
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange, ValidationError, Email, EqualTo
import names #for seeding users
from statistics import mean
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.model import BaseModelView

# CONFIG
app = Flask(__name__)
app.config.from_object(Config)



# Setup the Database:
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')

app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
us_holidays = holidays.US()

app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
admin = Admin(app, name='Admin', template_mode='bootstrap3')


lm = LoginManager()
lm.init_app(app)
login = LoginManager(app)
login.login_view = 'login'
oid = OpenID(app, os.path.join(basedir, 'tmp'))
# CONFIG


# FORMS
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    first = StringField('First Name', validators=[DataRequired()])
    last = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone Number')
    submit = SubmitField('Update')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    first = StringField('First Name', validators=[DataRequired()])
    last = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

# MODELS


class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, default=True)
    first = db.Column(db.String(128))
    last = db.Column(db.String(128))
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    created = db.Column(db.DateTime, index=False,
                        unique=False, default=date.today())
    phone = db.Column(db.Integer)
    qualified = db.Column(db.Boolean, index=True, unique=False, default=False)
    data = db.Column(db.String(2**30), index=False, unique=False)
    points = db.Column(db.Integer, index=True, unique=False, default=0)
    department = db.Column(db.String(128))
    point_offset = db.Column(db.Integer, default=0)
    roles=db.Column(db.String(128),default='')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_points(self,full_calendar):
        total_points=0
        for day in full_calendar:
            if day.assigned.get('DO')==self.id:
                total_points += day.value
        self.points=total_points+self.point_offset

    def __repr__(self):
        return f"{self.first} {self.last}"


class Day():
    def __init__(self, id, date):
        self.id = id
        self.date = date
        self.set_value()
        self.assigned = {}
        self.bid = {}

    def get_value(self, value=None):
        if self.date.weekday() > 4:
            return 3
        if self.date in us_holidays:
            return 3
        return 2

    def set_value(self, value=None):
        if value:
            self.value = value
        else:
            self.value = self.get_value()

    def insert_bid(self, user_id, bid=1):
        self.bid.update({user_id: bid})
        return None

    def assign_day(self, user_id, last):
        self.assigned = {"user_id": user_id, "last": last}
        return None

    def __repr__(self):
        return f"{self.date.strftime('%d %b %y')}"
# MODELS


class DutyUserView(ModelView):
    column_exclude_list = ['data','password_hash' ]
admin.add_view(DutyUserView(User, db.session))


# FUNCTIONS
start_date = date(2019, 1, 1)
days_of_week = "Mon, Tue, Wed, Thu, Fri, Sat, Sun".split(',')
@login.user_loader
def load_user(id=1):
    return User.query.get(int(id))


def get_date_index(my_date):
    result = my_date-start_date
    return result.days


def get_month_calendar(my_date=date.today()):
    first_dom = my_date-timedelta(days=my_date.day-1)
    last_dom = first_dom + \
        timedelta(days=monthrange(first_dom.year, first_dom.month)[1])
    #start_index = get_date_index(first_dom-timedelta(days=first_dom.weekday()))
    start_index = get_date_index(first_dom)
    end_index = get_date_index(last_dom)
    full_calendar=unpickle_var('calendar')
    month_calendar = full_calendar[start_index:end_index]
    return month_calendar


def pickle_var(my_var,file_name):
    with open(file_name + '.pickle', 'wb') as fp:
        pickle.dump(my_var, fp)
    return None


def unpickle_var(file_name):
    with open(file_name + '.pickle', 'rb') as fp:
        my_var = pickle.load(fp)
        return my_var


def update_user_bid_dict(u_id, user_bid_dict):
    json_text = json.dumps(user_bid_dict)
    User.query.get(u_id).data = json_text
    print(f"saving {u_id}******{user_bid_dict}")
    return None


def load_user_bid_dict(u_id):
    try:
        user_bid_dict = json.loads(User.query.get(u_id).data)
    except:
        user_bid_dict = {}
    user_bid_dict = {int(k): int(v) for k, v in user_bid_dict.items()}
    return user_bid_dict

def save_month(month_calendar):
    full_calendar=unpickle_var('calendar')
    start_index = month_calendar[0].id
    end_index = month_calendar[-1].id
    full_calendar[start_index:end_index+1]=month_calendar
    print(full_calendar[start_index:end_index+1])
    pickle_var(full_calendar,'calendar')
    return None

def update_all_points():
    full_calendar = unpickle_var('calendar')
    users = User.query.all()
    for u in users:
        u.update_points(full_calendar)
    return None

def seed_users(num):
    for n in range(num):
        first=names.get_first_name()
        user = User(email=first+"@gmail.com",
                    first=first, last=names.get_last_name())
        user.set_password("squirrel")
        db.session.add(user)
        db.session.commit()
    seed_calendars()
    return None

def seed_calendars():
    full_calendar=unpickle_var('calendar')
    users = User.query.all()
    for u in users:
        user_bid_dict={}
        for day in full_calendar:
            user_bid_dict.update({day.id:randint(0,2)})
        update_user_bid_dict(u.id,user_bid_dict)
    print("SEEDED calendars^^^^^^^^^^^^^")





# db.drop_all()
# db.create_all()
# seed_users(30)

try: 
    full_calendar = unpickle_var('calendar')
except:
    full_calendar = [Day(n, start_date + timedelta(days=n)) for n in range(365*15)]
pickle_var(full_calendar,'calendar')
# FUNCTIONS


########################  Routes ########################

@app.route('/', methods=['GET', 'POST'])
def index():
    full_calendar=unpickle_var('calendar')
    assigned_days = [day for day in full_calendar if day.assigned.get('DO')==current_user.id]
    assigned_days.reverse()
    print(assigned_days)
    return render_template('welcome.html',assigned_days=assigned_days,today=date.today())


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    form = ProfileForm()

    if form.validate_on_submit():
        current_user.first = form.first.data
        current_user.last = form.last.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data

    form.email.data = current_user.email
    form.phone.data = current_user.phone
    form.first.data = current_user.first
    form.last.data = current_user.last

    print(load_user_bid_dict(current_user.id))

    return render_template('profile.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    first=form.first.data, last=form.last.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/calendar/', defaults={'year': date.today().year, 'month': date.today().month})
@app.route('/calendar/<int:year>/<int:month>')
@login_required
def calendar(year, month):
    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1
    calendar= get_month_calendar(date(year, month, 1))
    user_bid_dict = load_user_bid_dict(current_user.id)
    return render_template('calendar.html', user_bid_dict=user_bid_dict,
                           calendar=calendar, days_of_week=days_of_week)


@app.route('/save', methods=["POST"])
def save():
    user_bid_dict = load_user_bid_dict(current_user.id)
    data = request.form.to_dict()
    for k, v in data.items():
        if v == '':
            v = 0
        user_bid_dict.update({int(k): int(v)})
    update_user_bid_dict(current_user.id, user_bid_dict)
    return redirect(request.referrer)


@app.route('/assign', defaults={'year': date.today().year, 'month': date.today().month})
@app.route('/assign/<int:year>/<int:month>')
@login_required
def assign(year,month):
    users = User.query.all()
    users.sort(key=lambda x: x.points)
    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1
    calendar= get_month_calendar(date(year, month, 1))
    days_by_user = {u.id:0 for u in users}
    for day in calendar:
        if day.assigned.get("DO"):
            days_by_user[day.assigned.get("DO")]+=1
    return render_template('assign.html', calendar=calendar, users=users, bids={u.id: load_user_bid_dict(u.id) for u in users},\
        days_by_user=days_by_user)

@app.route('/assign_gen/<int:clear>/<int:year>/<int:month>', methods=['POST'])
@login_required
def assign_month_duty(clear,year,month):
    month_calendar = get_month_calendar(date(int(year),int(month),1))
    users = User.query.all()

    if clear==1:
        for day in month_calendar:
            day.assigned={}
    else:
        bids={u.id: load_user_bid_dict(u.id) for u in users}
        ##this determines which days have the fewest preferences - they are assigned first
        day_need_list ={}
        for day in month_calendar:
            score = 0
            for u in users:
                score+=bids[u.id].get(day.id,0)
            day_need_list.update({day.id:score})
            #temp_points tracks [points, days assigned in months] for each user
        temp_points = {u.id:{'points':u.points, "m_days":0 } for u in users}
        month_calendar.sort(key=lambda x: day_need_list.get(x.id))
        for day in month_calendar:
            #high_point records [high bid, user id, and day point value]
            high_point = [-1,None,None]
            #each day we re-sort the users based on how many points they have
            users.sort(key=lambda x: temp_points.get(x.id).get('points')) # we must re sort for each day
            for u in users:
                for day_id,bid_value in bids.get(u.id).items():
                    if day_id==day.id:
                        if bid_value>high_point[0]:
                            high_point=[bid_value,u.id,day.value]
            day.assigned['DO']=high_point[1]
            temp_points.update({high_point[1]:{'points': temp_points.get(high_point[1]).get('points')+high_point[2],\
            'm_days':temp_points.get(high_point[1]).get('m_days')+1}})
        month_calendar.sort(key=lambda day: day.id)
    save_month(month_calendar)
    update_all_points()
    return redirect(request.referrer)

@app.route('/points', methods=["GET"])
@login_required
def points():
    users = User.query.all()
    average =0
    for u in users:
        average+=u.points
    average = average/len(users)
    users.sort(reverse=True,key=lambda x: x.points)
    return render_template('points.html', users=users,average=average)

@app.route('/change', methods=["POST"])
@login_required
def change():
    full_calendar=unpickle_var('calendar')
    day = full_calendar[int(request.form.get('day_id'))]
    day.assigned['DO']=int(request.form.get('user_id'))
    save_month([day])
    update_all_points()
    return redirect(request.referrer)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
