from flask import Flask, render_template, render_template_string, request, redirect, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from random import randint, choice
import os
from config import Config




app = Flask(__name__)
app.config.from_object(Config)

##Setup the Database:
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')

app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    # side = db.Column(db.Integer, index=True)
    # parking = db.Column(db.Integer, default=0)
    # fuel = db.Column(db.Boolean, default=False)
    # dta = db.Column(db.Boolean, default=False)
    # arm = db.Column(db.Boolean, default=False)
    # notes = db.Column(db.String(512), nullable=True)
    # flying = db.Column(db.Boolean, default=False)
    # ordnance = db.Column(db.String(64), default="")
    # remarks = db.Column(db.String(512), default="")
    # status = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return str(self.side)


def get_users():
    return { 'id':0, 'name':"Allan Elsberry", "points":0,"phone":2059015853, "email":'allan.elsberry@gmail.com',"trained":True}




@app.route('/')
def welcome():
    return render_template('welcome.html', user=get_users())


@app.route('/login', methods=['GET','POST'])
def login():
    return render_template('login.html', user=get_users())