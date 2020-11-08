import os
from flask import Flask, request, make_response, render_template, current_app, g

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

app = Flask(__name__)

# Main study
@app.route('/', methods = ['GET','POST'])
def study_main():
  return f"Hello world from Test App & Rafsal: <br />DB_USER={DB_USER} <br />DB_PASS={DB_PASS} <br /> DB_NAME={DB_NAME}"