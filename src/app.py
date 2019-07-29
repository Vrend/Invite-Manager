from flask import Flask

app = Flask(__name__)


@app.route('/')
def index():
    return 'Welcome to the Invite Manager'


@app.route('/login')
def login():
    return 'This is the login page'


@app.route('/createform')
def create_form():
    return 'Create your form here'


@app.route('/form')
def view_form():
    return 'Enter information here'
