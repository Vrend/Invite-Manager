from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import get_forms
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

# mysql config

db_config = open('../db-info', 'r')
db_secret_key = db_config.readline().strip()


app.config['MYSQL_HOST'] = db_config.readline().strip()
app.config['MYSQL_USER'] = db_config.readline().strip()
app.config['MYSQL_PASSWORD'] = db_config.readline().strip()
app.config['MYSQL_DB'] = db_config.readline().strip()
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

db_config.close()

mysql = MySQL(app)

forms = get_forms()

# secret key

app.secret_key = db_secret_key


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Not logged in', 'danger')
            return redirect(url_for('login'))
    return wrap


def is_logged_out(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' not in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('index'))
    return wrap


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/forms')
@is_logged_in
def view_forms():
    return render_template('forms.html', forms=forms)


@app.route('/create_form')
@is_logged_in
def create_form():
    return render_template('create_form.html')


@app.route('/forms/<string:id>/')
def view_form(id):
    return render_template('form.html', id=id)


@app.route('/register', methods=['GET', 'POST'])
@is_logged_out
def register():
    register_form = RegisterForm(request.form)
    if request.method == 'POST' and register_form.validate():
        name = register_form.name.data
        username = register_form.username.data
        email = register_form.email.data
        password = sha256_crypt.encrypt(str(register_form.password.data))

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)', (name, email, username, password))
        mysql.connection.commit()
        cur.close()

        flash('You are now registered and can login', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form=register_form)


@app.route('/login', methods=['GET', 'POST'])
@is_logged_out
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()
        result = cur.execute('SELECT * FROM users WHERE username=%s', [username])
        if result > 0:
            data = cur.fetchone()
            password = data['password']

            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                cur.close()
                return redirect(url_for('view_forms'))
            else:
                error = 'Incorrect Password'
                cur.close()
                return render_template('login.html', error=error)
        else:
            error = "No account with that username"
            cur.close()
            return render_template('login.html', error=error)
    return render_template('login.html')


@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=3, max=50)])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message="Passwords don't match"), validators.Length(min=5, max=50)])
    confirm = PasswordField('Confirm Password', )
