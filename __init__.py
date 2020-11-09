import os
import sys
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

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['EXPLAIN_TEMPLATE_LOADING'] = True
env = app.jinja_env
env.add_extension("jinja2.ext.loopcontrols") #Loop extension to enable {% break %}

app.app_context().push()
CORS(app)

db = SQLAlchemy()

file_handler = logging.FileHandler(filename=os.path.join(app.root_path,'logs/app_'+time.strftime('%d-%m-%Y-%H-%M-%S')+'.log'))
stdout_handler = logging.StreamHandler(sys.stdout)
handlers = [file_handler, stdout_handler]

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                    handlers=handlers)
logging.info("Server loading...")

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

# Database definition
class UserEntry(db.Model):
  __tablename__ = 'user_entry'
  user_id = db.Column(db.String(64), primary_key=True)
  condition = db.Column(db.String(64), nullable=True)
  timestamp = db.Column(db.DateTime())

  def __init__(self, user_id):
    self.user_id = user_id
    self.timestamp = pstnow()

  def __repr__(self):
    return "<UserEntry(user_id='%s', condition='%s', timestamp='%s')>" % (
      self.user_id, self.condition, self.timestamp)

class UserAnswer(db.Model):
  __tablename__ = "user_answer"
  answer_id = db.Column(db.Integer, primary_key=True)
  question_id = db.Column(db.String(16), nullable=False)
  answer = db.Column(db.String(128), nullable=False)
  timestamp = db.Column(db.DateTime())
  # Foreign key
  user_id = db.Column(db.String(64), db.ForeignKey('user_entry.user_id'))

  # Relationship
  userEntry = relationship("UserEntry", back_populates="answers")

  def __init__(self, question_id, answer):
    self.question_id = question_id
    self.answer = answer
    self.timestamp = pstnow()

  def __repr__(self):
    return "<UserAnswer(answer_id='%s', question_id='%s', answer='%s')>" % (
      self.answer_id, self.question_id, self.answer)

UserEntry.answers = relationship("UserAnswer", 
  order_by=UserAnswer.answer_id, 
  back_populates="userEntry",
  cascade="all, delete-orphan")

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

  logging.info("DB access string: %s" % app.config['SQLALCHEMY_DATABASE_URI'])
  db.init_app(app)

  # Create all database tables
  logging.info("Create DB tables...")
  db.create_all()

  # Initialize global application context
  logging.info("Initialize global application context...")
  with app.app_context():
    # within this block, current_app points to app.
    logging.info("App name: %s" % current_app.name)

  logging.info("Initialization complete, start the actual server...")

setup_app(app)

# Main study
@app.route('/test', methods = ['GET','POST'])
def test():
  # Generate user id
  #user_id = uuid.uuid1()

  # Add entry to db for user
  #userEntry = UserEntry(user_id=str(user_id))
  #userEntry.condition = "Cond 1"

  logging.info("Adding entry to DB...")
  #db.session.merge(userEntry)
  #db.session.commit()

  webHTML = "<b>Test-Almost all is ready!</b> <br />"
  webHTML += "DB_USER="+str(ENV_VARS.get('DB_USER'))+"<br />"
  webHTML += "DB_PASS="+str(ENV_VARS.get('DB_PASS'))+"<br />"
  webHTML += "DB_NAME="+str(ENV_VARS.get('DB_NAME'))+"<br />"
  webHTML += "TEST_VAR="+str(ENV_VARS.get('TEST_VAR'))+"<br />"

  return webHTML 

# Main study
@app.route('/', methods = ['GET','POST'])
def study_main():
  user_id = request.args.get('user_id')
  logging.info("User_id:" + str(user_id))

  page_no = safe_cast(request.args.get('page_no'), int)
  logging.info("Page no:" + str(page_no))

  if page_no == None:
    page_no = 1

  # Generate user id
  if user_id == None:
    user_id = uuid.uuid1()

    # Add entry to db for user
    userEntry = UserEntry(user_id=str(user_id))
    userEntry.condition = "Cond 1"

    logging.info("Adding entry to DB...")
    db.session.merge(userEntry)
    db.session.commit()

  return render_template('study_main.html', user_id=user_id, page_no=page_no)

# Study page
@app.route('/study_page', methods = ['GET','POST'])
def study_page():
  user_id = request.args.get('user_id')
  logging.info("User_id:"+str(user_id))

  page_no = safe_cast(request.args.get('page_no'), int)
  logging.info("Page no:"+str(page_no))

  pages = ['p1_introduction.html', 'p2_chat_interaction.html', 'p3_survey.html',
           'p5_conv_on_side.html', ]

  template = "No such page!"
  if page_no > 0 and page_no <= len(pages):
    add_answer(user_id, "P"+str(page_no), "Yes")
    
    questions = []
    if pages[page_no-1] == 'p3_survey.html':
      questions = [ "I was really drawn into answering questions", 
                    "I felt involved in answering questions",
                    "This experience of answering questions was fun",
                    "I forgot about my immediate surroundings while answering questions",
                    "I was so involved in answering questions that I ignored everything around me",
                    "I was absorbed in answering questions"
                  ]

    template = render_template(pages[page_no-1], user_id=user_id, page_no=page_no, questions=questions)

  elif page_no > len(pages):
    #Study completed!
    add_answer(user_id, "P"+str(page_no), "Completed")
    template = render_template('p6_completed.html', user_id=user_id, page_no=page_no, token='4654334445')

  return template

# Load the conversational survey
@app.route("/get_survey")
def get_survey():
  logging.info("Trying to get survey..")

  survey_file = request.args.get('survey_file')
  json_resp = json.dumps({'status': 'ERROR', 'message':''})

  if survey_file != None:
    logging.info("Survey file:"+str(survey_file))

    survey_path = './static/surveys'

    survey_dict = ""
    with open(survey_path+"/"+survey_file, 'r', encoding='utf-8') as f:
      survey_dict = json.load(f)

    json_resp = json.dumps({'status': 'OK', 'message':'', 'survey_data':survey_dict})
  else:
    json_resp = json.dumps({'status': 'ERROR', 'message':'Missing arguments'})

  return make_response(json_resp, 200, {"content_type":"application/json"})

@app.route('/get_study_responses')
def get_study_responses():
  key_values = ['user_id','condition','datetime']
  entry_values = []
  
  allEntries = UserEntry.query.order_by(UserEntry.user_id.desc(), UserEntry.timestamp.desc()).limit(1000)
  for entry in allEntries:
    #print("Ticker ID:"+alarm.ticker_id)

    for ans in entry.answers:
      if ans.question_id not in key_values:
        key_values.append(ans.question_id)

    values = ['' for v in key_values]
    values[0] = entry.user_id
    values[1] = entry.condition
    values[2] = entry.timestamp

    for ans in entry.answers:
      key_idx = key_values.index(ans.question_id)
      values[key_idx] = ans.answer
      

    entry_values.append(values)

  logging.info("Key Values:", key_values)
  logging.info("Entry Values:", entry_values)

  return render_template('study_responses.html', headers=key_values, entries=entry_values)

# Helper methods
def add_answer(user_id, q_id, ans):
  userEntry = UserEntry.query.get(user_id)

  if userEntry != None:
    userAnswer = UserAnswer(question_id=q_id, answer=ans)
    userEntry.answers.append(userAnswer)
    db.session.commit()

# Cast string to int
def safe_cast(val, to_type, default=None):
  try:
    return to_type(val)
  except (ValueError, TypeError):
    return default