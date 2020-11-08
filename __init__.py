from flask import Flask, request, make_response, render_template, current_app, g

app = Flask(__name__)

# Main study
@app.route('/', methods = ['GET','POST'])
def study_main():
  return "Hello world from Test App & Rafsal!"