import os
from flask import Flask, request, make_response, render_template, current_app, g

ENV_VARS = {}

app = Flask(__name__)

def load_env(filename):
  with open(filename) as myfile:
    for line in myfile:
      name, var = line.rstrip('\n').partition("=")[::2]
      ENV_VARS[name.strip()] = var
 
# Server instance initialize
def setup_app(app):  
  print("Loading the server, first init global vars...")
  print("Root path:", app.root_path)
  load_env(os.path.join(app.root_path,"variables.env"))


  print("Start the actual server...")

setup_app(app)

# Main study
@app.route('/', methods = ['GET','POST'])
def study_main():
  webHTML = "Hello world from Test App & Rafsal: <br />"
  webHTML += "DB_USER="+str(ENV_VARS.get('DB_USER'))+"<br />"
  webHTML += "DB_PASS="+str(ENV_VARS.get('DB_PASS'))+"<br />"
  webHTML += "DB_NAME="+str(ENV_VARS.get('DB_NAME'))+"<br />"
  webHTML += "TEST_VAR="+str(ENV_VARS.get('TEST_VAR'))+"<br />"

  return webHTML 