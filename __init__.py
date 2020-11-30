import os
import sys
import logging
import random
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
from sqlalchemy import func
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

conditions = ["_big_5_conv.json", "_fitness_survey_conv.json", "_personal_financial_survey_conv.json", 
  "_political_views_conv.json", "_pvq_values_conv.json", "_sleep_quality_conv.json"]

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
  question_id = db.Column(db.String(64), nullable=False)
  answer = db.Column(db.String(10000), nullable=False)
  timestamp = db.Column(db.DateTime())
  # Foreign key
  user_id = db.Column(db.String(64), db.ForeignKey('user_entry.user_id'))

  # Relationship
  userEntry = relationship("UserEntry", back_populates="answers") #backref=db.backref('answers', lazy='dynamic')

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
  #lazy='dynamic',
  #passive_deletes=True,
  cascade="all, delete-orphan")

class ChatAnswer(db.Model):
  __tablename__ = "chat_answer"
  answer_id = db.Column(db.Integer, primary_key=True)
  question_id = db.Column(db.String(1024), nullable=False)
  answer = db.Column(db.String(10000), nullable=False)
  option_id = db.Column(db.String(1024), nullable=False)
  timestamp = db.Column(db.DateTime())
  # Foreign key
  user_id = db.Column(db.String(64), db.ForeignKey('user_entry.user_id'))

  # Relationship
  userEntry = relationship("UserEntry", back_populates="chatAnswers") #backref=db.backref('answers', lazy='dynamic')

  def __init__(self, question_id, answer, option_id):
    self.question_id = question_id
    self.answer = answer
    self.option_id = option_id
    self.timestamp = pstnow()

  def __repr__(self):
    return "<ChatAnswer(answer_id='%s', question_id='%s', answer='%s', option_id='%s')>" % (
      self.answer_id, self.question_id, self.answer)

UserEntry.chatAnswers = relationship("ChatAnswer", 
  order_by=ChatAnswer.answer_id, 
  back_populates="userEntry",
  #lazy='dynamic',
  #passive_deletes=True,
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
@app.route('/', methods = ['GET','POST'])
def study_main():
  user_id = request.args.get('user_id')
  logging.info("User_id:" + str(user_id))

  page_no = safe_cast(request.args.get('page_no'), int)
  logging.info("Page no:" + str(page_no))

  condition_id = request.args.get('condition_id')
  logging.info("Condition ID:" + str(condition_id))

  if page_no == None:
    page_no = 1

  # try getting the user_id from the cookie
  user_id = request.cookies.get('user_id')
  if user_id != None:
    logging.info("Got user id from cookie:"+user_id)
  else:
    # Generate user id 
    user_id = uuid.uuid1()
    logging.info("Generated user id:"+str(user_id))

    # get condition - random, provided or existing db
    condition_id = getCondition(condition_id, user_id)

    # Add entry to db for user
    userEntry = UserEntry(user_id=str(user_id))
    userEntry.condition = condition_id

    logging.info("Adding entry to DB...")
    db.session.merge(userEntry)
    db.session.commit()

  # get condition - random, provided or existing db
  condition_id = getCondition(condition_id, user_id)

  # get the last study page visited
  page_no = getLastStudyPage(user_id)

  resp = make_response(render_template('study_main.html', user_id=user_id, page_no=page_no, condition_id=condition_id))
  resp.set_cookie('user_id', str(user_id))
  return resp

def getCondition(condition_id, user_id):
  # Get condition - not given as param, take from DB
  if condition_id == None:
    entry = UserEntry.query.get(str(user_id))
    if entry:
      condition_id = entry.condition
    else:
      # Get the existing conditions
      conditionCounts = dict((cond,0) for cond in conditions) 
      completedAnswers = UserAnswer.query.filter_by(question_id="complete", answer="true")
      for ans in completedAnswers:
        conditionCounts[ans.userEntry.condition] += 1

      logging.info("Conditions counts:" + str(conditionCounts))

      sorted_by_freq = sorted(conditionCounts.items(), key=lambda kv: kv[1], reverse = False)
      least_freq = None
      choices = []

      logging.info("Sorted counts:" + str(sorted_by_freq))

      for cond, freq in sorted_by_freq:
        if least_freq == None:
          least_freq = freq
        
        if freq <= least_freq:
          choices.append(cond)

      logging.info("Condition choices:" +str(choices))

      condition_id = random.choice(choices)

      # Randomly select condition
      #condition_id = random.choice(conditions)

  return condition_id

def getLastStudyPage(user_id):
  entry = UserEntry.query.get(str(user_id))
  page_no = 1
  for ans in entry.answers:
    if ans.question_id == "page":
      page_no = ans.answer

  return page_no

# Clear cookie - just for dev
@app.route('/clear_cookie')
def clear_cookie():
  resp = make_response("<b>Cookie cleared!</b>")
  resp.set_cookie('user_id', '', expires=0)
  return resp

# Study page
@app.route('/study_page', methods = ['GET','POST'])
def study_page():
  user_id = request.args.get('user_id')
  logging.info("User_id:"+str(user_id))

  page_no = safe_cast(request.args.get('page_no'), int)
  logging.info("Page no:"+str(page_no))

  condition_id = request.args.get('condition_id')
  logging.info("Condition ID:" + str(condition_id))

  pages = ['p1_introduction.html', 'p2_chat_interaction.html', 'p3_survey.html',
           'p4_sus.html', 'p5_conv_on_side.html', ]

  template = "No such page!"
  if page_no > 0 and page_no <= len(pages):
    add_survey_answer(user_id, "page", str(page_no))
    add_survey_answer(user_id, "complete", "false", replace=True)
    
    questions = []
    if pages[page_no-1] == 'p3_survey.html':
      questions = [ "I was really drawn into answering questions", 
                    "I felt involved in answering questions",
                    "This experience of answering questions was fun",
                    "I forgot about my immediate surroundings while answering questions",
                    "I was so involved in answering questions that I ignored everything around me",
                    "I was absorbed in answering questions"
                  ]
    elif pages[page_no-1] == 'p4_sus.html':
      questions = [ "I think that I would like to use this chat interaction frequently.", 
                    "I found the chat interaction unnecessarily complex.",
                    "I thought the chat interaction was easy to use.",
                    "I think that I would need the support of a technical person to be able to use this chat interaction.",
                    "I found the various functions in this chat interaction were well integrated.",
                    "I thought there was too much inconsistency in this chat interaction.",
                    "I would imagine that most people would learn to use this chat interaction very quickly.",
                    "I found the chat interaction very cumbersome to use.",
                    "I felt very confident using the chat interaction.",
                    "I needed to learn a lot of things before I could get going with this chat interaction.",
                    "If you are reading this, please select 'Agree'"
                  ]

    #randomize question ordering
    random.shuffle(questions)

    template = render_template(pages[page_no-1], user_id=user_id, page_no=page_no, questions=questions, condition_id=condition_id)

  elif page_no > len(pages):
    #Study completed!
    add_survey_answer(user_id, "page", str(page_no))
    add_survey_answer(user_id, "complete", "true", replace=True)
    template = render_template('p6_completed.html', user_id=user_id, page_no=page_no, token=user_id)

  return template

# Load question-part
@app.route('/question_part', methods = ['GET','POST'])
def question_part():
  q_no = request.args.get('q_no')
  logging.info("q_no:"+str(q_no))

  total_q_no = request.args.get('total_q_no')
  logging.info("total_q_no:"+str(total_q_no))

  h_part = request.args.get('h_part')
  logging.info("h_part:"+str(h_part))

  q_desc = request.form.get('q_desc')
  logging.info("q_desc:"+str(q_desc))

  q_final = request.args.get('q_final')
  logging.info("q_final:"+str(q_final))

  return render_template('question_part.html', q_no=q_no, total_q_no=total_q_no, q_desc=q_desc, h_part=h_part, q_final=q_final)

# Load the conversational survey
@app.route("/get_survey")
def get_survey():
  logging.info("Trying to get survey..")

  survey_file = request.args.get('survey_file')
  json_resp = json.dumps({'status': 'ERROR', 'message':''})

  if survey_file != None:
    logging.info("Survey file:"+str(survey_file))

    survey_path = os.path.join(app.root_path,'static/surveys')

    survey_dict = ""
    with open(survey_path+"/"+survey_file, 'r', encoding='utf-8') as f:
      survey_dict = json.load(f)

    json_resp = json.dumps({'status': 'OK', 'message':'', 'survey_data':survey_dict})
  else:
    json_resp = json.dumps({'status': 'ERROR', 'message':'Missing arguments'})

  return make_response(json_resp, 200, {"content_type":"application/json"})

@app.route('/get_chat_answers')
def get_chat_answers():
  logging.info("Getting chat answers...")

  user_id = request.args.get('user_id')
  logging.info("User_id:"+str(user_id))

  question_answers = {}
  chatAnswers = ChatAnswer.query.filter_by(user_id=user_id)
  for ans in chatAnswers:
    question_answers[ans.question_id] = {"text": ans.answer, "opt_id": ans.option_id}

  json_resp = json.dumps({'status': 'OK', 'message':'', 'chat_answers':question_answers})
  
  return make_response(json_resp, 200, {"content_type":"application/json"})

@app.route('/get_study_responses')
def get_study_responses():
  key_values = ['user_id','condition','datetime','duration (min)','last_activity (h)']
  entry_values = []

  # Get the responses
  allEntries = UserEntry.query.order_by(UserEntry.timestamp.desc()).limit(1000)
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
      
    #get duration from start till last activity
    last_activity = db.session.query(UserAnswer)\
      .filter(UserAnswer.user_id == entry.user_id)\
        .order_by(UserAnswer.timestamp.desc()).first()

    logging.info("Last activity:"+ str(last_activity.timestamp)+", start:"+str(entry.timestamp))
    duration = round((last_activity.timestamp - entry.timestamp).total_seconds() / 60.0,2)
    values[3] = duration

    #get elapsed time since last activity
    #print("Now:", datetime.now())
    values[4] = round((pstnow() - last_activity.timestamp).total_seconds() / (60.0*60.0),2)

    entry_values.append(values)

  #logging.info("Key Values:"+ str(key_values))
  #logging.info("Entry Values:"+str(entry_values))

  # Get the summary of responses per condition
  conditionCounts = dict((cond,{"all":0, "complete":0, "pending":0, "pending_old":0, "pending_fresh":0}) for cond in conditions) 
  allAnswers = UserAnswer.query.filter_by(question_id="complete")
  for ans in allAnswers:
    conditionCounts[ans.userEntry.condition]["all"] += 1
    if ans.answer == "true":
      conditionCounts[ans.userEntry.condition]["complete"] += 1
    elif ans.answer == "false":
      conditionCounts[ans.userEntry.condition]["pending"] += 1
      #last activity
      last_activity = db.session.query(UserAnswer)\
        .filter(UserAnswer.user_id == ans.user_id)\
          .order_by(UserAnswer.timestamp.desc()).first()

      #likely expired
      minutes_passed = (pstnow() - last_activity.timestamp).total_seconds() / 60.0
      if (minutes_passed > 60):
        conditionCounts[ans.userEntry.condition]["pending_old"] += 1
      else:
        conditionCounts[ans.userEntry.condition]["pending_fresh"] += 1

  logging.info("Conditions counts:" + str(conditionCounts))

  return render_template('study_responses.html', headers=key_values, entries=entry_values, condition_summary=conditionCounts)

# Add answer
@app.route('/save_answer', methods = ['GET','POST'])
def save_answer():
  logging.info("Trying to save answer...")

  user_id = request.args.get('user_id')
  logging.info("user_id:"+str(user_id))

  source = request.args.get('source')
  logging.info("source:"+str(source))

  q_id = request.args.get('q_id')
  print("q_id:",str(q_id))

  q_ans = request.form.get('q_ans')
  print("q_ans:",str(q_ans))

  opt_id = request.form.get('opt_id')
  print("Answer option id:",str(opt_id))

  json_resp = json.dumps({'status': 'ERROR', 'message':''})
  save_result = False
  if source == "chat":
    save_result = add_chat_answer(user_id, q_id, q_ans, opt_id, replace=True)
  else:
    save_result = add_survey_answer(user_id, q_id, q_ans, replace=True)

  if save_result:
    json_resp = json.dumps({'status': 'OK', 'message':'', 'q_id':q_id, 'q_ans':q_ans})
  else:
    json_resp = json.dumps({'status': 'ERROR', 'message':'Missing arguments'})

  return make_response(json_resp, 200, {"content_type":"application/json"})

# Helper method - add survey answer
def add_survey_answer(user_id, q_id, ans, replace=False):
  userEntry = UserEntry.query.get(user_id)

  if userEntry != None:
    userAnswer = UserAnswer(question_id=q_id, answer=ans)
    
    found = False
    for answer in userEntry.answers:
      if answer.question_id == q_id:
        if replace == True:
          answer.answer = ans
          found = True
        else:
          if answer.answer == ans:
            found = True
      
    # answer does not exist yet
    if found == False:
      userEntry.answers.append(userAnswer)

    db.session.commit()

    return True
  else:
    return False

# Helper method - add chat answer
def add_chat_answer(user_id, q_id, ans, opt_id, replace=False):
  userEntry = UserEntry.query.get(user_id)

  if userEntry != None:
    chatAnswer = ChatAnswer(question_id=q_id, answer=ans, option_id=opt_id)
    
    found = False
    for answer in userEntry.chatAnswers:
      if answer.question_id == q_id:
        if replace == True:
          answer.answer = ans
          found = True
        else:
          if answer.answer == ans:
            found = True
      
    # answer does not exist yet
    if found == False:
      userEntry.chatAnswers.append(chatAnswer)

    db.session.commit()

    return True
  else:
    return False

# Cast string to int
def safe_cast(val, to_type, default=None):
  try:
    return to_type(val)
  except (ValueError, TypeError):
    return default