from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from random import randint, choice
import os
from config import Config
from datetime import date, timedelta
from calendar import monthrange
from flask_migrate import Migrate





app = Flask(__name__)
app.config.from_object(Config)

##Setup the Database:
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')

app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app,db)
full_calendar = [date(2019,1,1) + timedelta(days=n) for n in range(365*15)]

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(128), nullable=False)
    last = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    created = db.Column(db.DateTime, index=False, unique=False, nullable=False, default=date.today())
    phone = db.Column(db.Integer)
    qualified = db.Column(db.Boolean, index=True, unique=False, default=False)
    data = db.Column(db.BLOB, index=False, unique=False)
    points = db.Column(db.Integer, index=True, unique=False, default=0)
    
    def __repr__(self):
        return f"{self.first} {self.last}"


def get_user():
    return User.query.get(1)

def create_user(u):
    db.session.add(u)

def seed_users():
    u = User(first="Allan",last="Elsberry",email="allan.elsberry@gmail.com",phone=2059015853,qualified=True)
    create_user(u)
    return None

def get_calendar(day=date.today()):
    calendar = {}
    days_of_week = "Mon, Tue, Wed, Thu, Fri, Sat, Sun".split(',')
    start_date = day= day-timedelta(days=(day.day-1)) #get beginning of month
    date_list = [start_date+timedelta(days=n) for n in range(monthrange(start_date.year,start_date.month)[1])]
    calendar.update({'date_list':date_list})
    calendar.update({'days_of_week':days_of_week})
    return calendar
    
#seed_users()



########################  Routes ########################

@app.route('/')
def welcome():
    return render_template('welcome.html', user=get_user())


@app.route('/login', methods=['GET','POST'])
def login():
    return render_template('login.html', user=get_user())

@app.route('/calendar')
def calendar():
    return render_template('calendar.html', user=get_user(), calendar = get_calendar())