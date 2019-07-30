import sys
import uuid
from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from data import gen_options, check_unique_user
from flask_mysqldb import MySQL
from wtforms import Form, StringField, PasswordField, validators, widgets, SelectMultipleField, IntegerField
from passlib.hash import sha256_crypt
from functools import wraps

# Check if in debug mode

debug = False
try:
    debug_param = sys.argv[1]
    if debug_param == 'debug':
        debug = True
except IndexError:
    debug = False

app = Flask(__name__)

# mysql config

db_config = open('../db-info', 'r')

app.secret_key = db_config.readline().strip()
app.config['MYSQL_HOST'] = db_config.readline().strip()
app.config['MYSQL_USER'] = db_config.readline().strip()
app.config['MYSQL_PASSWORD'] = db_config.readline().strip()

mysql_db = db_config.readline().strip()

app.config['MYSQL_DB'] = mysql_db
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

db_config.close()

mysql = MySQL(app)


# Wrappers for sessions
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

# Site index
@app.route('/')
def index():
    return render_template('home.html')

# About page
@app.route('/about')
def about():
    return render_template('about.html')

# View all available forms
@app.route('/forms')
@is_logged_in
def view_forms():
    cur = mysql.connection.cursor()

    result = cur.execute('SELECT * FROM forms WHERE user=%s', [session['username']])
    forms = cur.fetchall()
    cur.close()
    if result > 0:
        return render_template('forms.html', forms=forms)
    else:
        msg = 'No forms found :('
        return render_template('forms.html', msg=msg)


# Create a form here
@app.route('/create_form', methods=['GET', 'POST'])
@is_logged_in
def create_form():
    form = FormCreationForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        uses = form.uses.data
        options = gen_options(form.data.data)
        form_id = uuid.uuid1().hex

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO forms(id, user, name, data, uses, max_uses) VALUES(%s, %s, %s, %s, 0, %s)', (form_id, session['username'], name, options, uses))
        mysql.connection.commit()
        cur.close()
        flash('Form Created', 'success')
        return redirect(url_for('index'))

    return render_template('create_form.html', form=form)

# Delete a form
@app.route('/delete_form/<string:id>/', methods=['POST'])
@is_logged_in
def delete_form(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM forms WHERE id = %s AND user = %s', [id, session['username']])
    mysql.connection.commit()
    cur.close()
    flash('Form Deleted', 'success')
    return redirect(url_for('view_forms'))

# View a specific form
@app.route('/forms/<string:id>/')
@is_logged_in
def view_form(user_id):
    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * FROM forms WHERE id = %s AND user = %s', [user_id, session['username']])
    if result > 0:
        form = cur.fetchone()
        return render_template('form.html', form=form)
    else:
        flash('Form is Unavailable', 'danger')
        return redirect(url_for('index'))

# Register an account
@app.route('/register', methods=['GET', 'POST'])
@is_logged_out
def register():
    register_form = RegisterForm(request.form)
    if request.method == 'POST' and register_form.validate():
        name = register_form.name.data
        username = register_form.username.data
        email = register_form.email.data
        password = sha256_crypt.encrypt(str(register_form.password.data))

        if not check_unique_user(username, email, mysql):
            flash('Username or email already taken', 'danger')
            return redirect(url_for('register'))

        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)', (name, email, username, password))
        mysql.connection.commit()
        cur.close()

        flash('You are now registered and can login', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form=register_form)

# Login on this page
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
                return redirect(url_for('index'))
            else:
                error = 'Incorrect Password'
                cur.close()
                return render_template('login.html', error=error)
        else:
            error = "No account with that username"
            cur.close()
            return render_template('login.html', error=error)
    return render_template('login.html')

# Logout on this page
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))


@app.route('/user_settings')
@is_logged_in
def user_settings():
    return render_template('user_settings.html')


@app.route('/delete_account', methods=['POST'])
@is_logged_in
def delete_account():
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM forms WHERE user = %s', [session['username']])
    cur.execute('DELETE FROM users WHERE username = %s', [session['username']])
    mysql.connection.commit()
    session.clear()
    flash('Account Successfully Deleted', 'success')
    cur.close()
    return redirect(url_for('index'))


@app.before_first_request
def check_if_user_table_exists():
    cur = mysql.connection.cursor()
    result = cur.execute('SHOW TABLES LIKE \'users\'')
    if result < 1:
        print('Creating User Table...')
        cur.execute('CREATE TABLE users(id INT(12) AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), email VARCHAR(100), username VARCHAR(30), password VARCHAR(100))')
        mysql.connection.commit()
    else:
        print('Loading User table...')
    result = cur.execute('SHOW TABLES LIKE \'forms\'')
    if result < 1:
        print('Creating Forms Table...')
        cur.execute('CREATE TABLE forms(id VARCHAR(50) PRIMARY KEY, user VARCHAR(30), name VARCHAR(50), data VARCHAR(25), uses INT(10), max_uses INT(10))')
        mysql.connection.commit()
    else:
        print('Loading Forms Table...')
    cur.close()


# Registration form
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=3, max=50), validators.email(message="Must be a Valid Email")])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message="Passwords don't match"), validators.Length(min=5, max=50)])
    confirm = PasswordField('Confirm Password', )


class CheckBoxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class FormCreationForm(Form):
    name = StringField('Form Name', [validators.Length(min=1, max=50)])
    options = [(1, 'picture'), (2, 'name'), (3, 'email'), (4, 'Phone #'), (5, 'School')]
    data = CheckBoxField('Field Options', choices=options, coerce=int)
    uses = IntegerField('Form Uses', [validators.DataRequired(message='Give a number, -1 for infinite uses'), validators.NumberRange(min=-1)])


@app.errorhandler(404)
def handle_404(e):
    flash('Page is unauthorized or doesn\'t exist. Check spelling or try again', 'danger')
    return redirect(url_for('index'))


@app.errorhandler(405)
def handle_405(e):
    flash('Page is unauthorized or doesn\'t exist. Check spelling or try again', 'danger')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=debug)
