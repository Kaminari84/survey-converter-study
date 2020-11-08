import os
from flask import Flask, request, make_response, render_template, current_app, g

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

app = Flask(__name__)

# Main study
@app.route('/', methods = ['GET','POST'])
def study_main():
  webHTML = "Hello world from Test App & Rafsal: <br />"
  webHTML += "DB_USER="+str(DB_USER)+"<br />"
  webHTML += "DB_PASS="+str(DB_PASS)+"<br />"
  webHTML += "DB_NAME="+str(DB_NAME)+"<br />"

  return webHTML 