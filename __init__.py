import os
import logging
import json
import uuid
from datetime import datetime
import time
import pytz
from datetime import datetime, timedelta
from pytz import timezone
from pytz import common_timezones
from pytz import country_timezones

from flask import Flask, request, make_response, render_template, current_app, g
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy.orm import relationship

from flask_cors import CORS

ENV_VARS = {}
app = Flask(__name__)
db = None

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['EXPLAIN_TEMPLATE_LOADING'] = True
env = app.jinja_env
env.add_extension("jinja2.ext.loopcontrols") #Loop extension to enable {% break %}

app.app_context().push()
CORS(app)

logging.basicConfig(filename=os.path.join(app.root_path,'logs/app_'+time.strftime('%d-%m-%Y-%H-%M-%S')+'.log'), level=logging.INFO)
logging.info("Server loading...")
 
# Server instance initialize
def setup_app(app):  
  global db

  logging.info("Initializing the server, first load env variables...")
  logging.info("Root path: %s" % app.root_path)
  
  # Load environmental variables
  load_env(os.path.join(app.root_path,"variables.env"))

  # Initialize the database
  logging.info("Initialize the database...")

  db_name = ENV_VARS.get('DB_NAME')
  db_user = ENV_VARS.get('DB_USER')
  db_pass = ENV_VARS.get('DB_PASS')

  app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://"+str(db_user)+":"+str(db_pass)+"@127.0.0.1:3306/"+str(db_name)
  app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
  app.config['SQLALCHEMY_POOL_RECYCLE'] = 1

  db = SQLAlchemy(app)

  # Create all database tables
  logging.info("Create DB tables...")



  # Initialize global application context
  logging.info("Initialize global application context...")
  with app.app_context():
    # within this block, current_app points to app.
    logging.info("App name: %s" % current_app.name)

  logging.info("Initialization complete, start the actual server...")

# Main study
@app.route('/', methods = ['GET','POST'])
def study_main():
  webHTML = "Hello world from Test App & Rafsal: <br />"
  webHTML += "DB_USER="+str(ENV_VARS.get('DB_USER'))+"<br />"
  webHTML += "DB_PASS="+str(ENV_VARS.get('DB_PASS'))+"<br />"
  webHTML += "DB_NAME="+str(ENV_VARS.get('DB_NAME'))+"<br />"
  webHTML += "TEST_VAR="+str(ENV_VARS.get('TEST_VAR'))+"<br />"

  return webHTML 

# Load environmental variables
def load_env(filename):
  with open(filename) as myfile:
    for line in myfile:
      name, var = line.rstrip('\n').partition("=")[::2]
      ENV_VARS[name.strip()] = var

# Date-Time helpers
def utcnow():
    return datetime.now(tz=pytz.utc)

def pstnow():
    utc_time = utcnow()
    pacific = timezone('US/Pacific')
    pst_time = utc_time.astimezone(pacific)
    return pst_time

setup_app(app)