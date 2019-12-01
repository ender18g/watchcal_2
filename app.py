from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, abort
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
us_holidays = holidays.US()

class User(db.Model):
    __tablename__='Users'
    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(128), nullable=False)
    last = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    created = db.Column(db.DateTime, index=False, unique=False, nullable=False, default=date.today())
    phone = db.Column(db.Integer)
    qualified = db.Column(db.Boolean, index=True, unique=False, default=False)
    data = db.Column(db.String(32768), index=False, unique=False)
    points = db.Column(db.Integer, index=True, unique=False, default=0)
    
    def __repr__(self):
        return f"{self.first} {self.last}"

class Day():
    def __init__(self,id,date):
        self.id=id
        self.date=date
        self.set_value()
        self.assigned={}
        self.bid = {}
    def get_value(self,value=None):
        if self.date.weekday()>4:
            return 3
        if self.date in us_holidays:
            return 3
        return 2
    def set_value(self,value=None):
        if value:
            self.value=value 
        else:
            self.value=self.get_value()
    def insert_bid(self,user_id,bid=1):
        self.bid.update({user_id:bid})
        return None
    def assign_day(self,user_id,last):
        self.assigned={"user_id": user_id, "last": last}
        return None
    def __repr__(self):
        return f"{self.date.strftime('%d %b %y')}"



start_date = date(2019,1,1)
days_of_week = "Mon, Tue, Wed, Thu, Fri, Sat, Sun".split(',')


def get_user():
    return User.query.get(1)

def create_user(u):
    global db
    db.session.add(u)
    db.session.commit()

def seed_users():
    u = User(first="Allan",last="Elsberry",email="allan.elsberry@gmail.com",phone=2059015853,qualified=True)
    create_user(u)
    return None
def get_date_index(my_date):
    result = my_date-start_date
    return result.days
def get_month_calendar(my_date=date.today()):
    first_dom = my_date-timedelta(days=my_date.day-1)
    last_dom = first_dom+timedelta(days=monthrange(first_dom.year,first_dom.month)[1])
    start_index = get_date_index(first_dom-timedelta(days=first_dom.weekday()))
    end_index = get_date_index(last_dom)
    month_calendar = full_calendar[start_index:end_index]
    return [month_calendar,{'first_dom':first_dom,'start_index':get_date_index(first_dom)}]
def pickle_calendar(full_calendar):
    with open('calendar.pickle','wb') as fp:
        pickle.dump(full_calendar,fp)
    return None
def unpickle_calendar():
    with open('calendar.pickle','rb') as fp:
        full_calendar = pickle.load(fp)
        return full_calendar
def update_user_bid_dict(u_id,user_bid_dict):
    with open(f"{u_id}.json","w") as f:
        json.dump(user_bid_dict,f)
    print(f"saving {u_id}******{user_bid_dict}")
    return None
def get_user_bid_dict(u_id): 
    try:
        with open(f"{u_id}.json","r") as f:
            user_bid_dict = json.load(f)
        user_bid_dict={int(k):int(v) for k,v in user_bid_dict.items()}
    except: return {}
    return user_bid_dict

# db.drop_all()
# db.create_all()
# seed_users()
try:
    full_calendar = unpickle_calendar()
except: 
    full_calendar = [Day(n,start_date + timedelta(days=n)) for n in range(365*15)]

########################  Routes ########################

@app.route('/', methods=['GET','POST'])
def welcome():
    current_user = get_user()
    if request.method =="POST":
        current_user.first=request.form['name']
        print(request.form['name'])
        db.session.commit()
    return render_template('welcome.html', user=get_user())


@app.route('/login', methods=['GET','POST'])
def login():
    return render_template('login.html', user=get_user())

@app.route('/calendar/',defaults={'year':date.today().year, 'month':date.today().month})
@app.route('/calendar/<int:year>/<int:month>')
def calendar(year,month):
    if month>12:
        month=1
        year+=1
    elif month<1:
        month=12
        year-=1
    calendar,start_info = get_month_calendar(date(year,month,1))
    current_user = get_user()
    user_bid_dict = get_user_bid_dict(current_user.id)
    return render_template('calendar.html', user=get_user(), user_bid_dict = user_bid_dict, 
        calendar = calendar,start_info=start_info,days_of_week=days_of_week)

@app.route('/save', methods=["POST"])
def save():
    current_user = get_user()
    user_bid_dict = get_user_bid_dict(current_user.id)
    data = request.form.to_dict()
    for k,v in data.items():
        if v == '':
            v=0
        user_bid_dict.update({int(k):int(v)})
    update_user_bid_dict(current_user.id,user_bid_dict)
    return redirect(request.referrer)


@app.route('/assign', methods=["POST"])
def assign():
    pickle_calendar(full_calendar)