import uuid
from flask import Flask, render_template, flash, redirect, url_for, session, abort
from data import *
from access import *
from flask_mysqldb import MySQL
from site_forms import *
from passlib.hash import sha256_crypt
from flask_qrcode import QRcode

app = Flask(__name__)

args = handle_args()
debug_enabled = args[0]
allow_registration = args[1]
show_help = args[2]

# Site index
@app.route('/')
def index():
    return render_template('home.html', allow_registration=allow_registration)

# About page
@app.route('/about')
def about():
    return render_template('about.html', allow_registration=allow_registration)

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

        if 't' not in options:
            flash('You require at least one form field', 'danger')
        else:
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO forms(id, user, name, data, uses, max_uses) VALUES(%s, %s, %s, %s, 0, %s)', (form_id, session['username'], name, options, uses))
            statement = create_form_table(options, form_id)
            try:
                cur.execute(statement)
            except:
                print(statement)
                flash('Failed to Create Form')
                redirect(url_for('create_form'))

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
    result = cur.execute('SELECT * FROM forms WHERE id = %s AND user = %s', [id, session['username']])
    if result > 0:
        cur.execute('DELETE FROM links WHERE form_id = %s AND user = %s', [id, session['username']])
        cur.execute('DELETE FROM forms WHERE id = %s AND user = %s', [id, session['username']])
        cur.execute('DELETE FROM qrhash WHERE form = %s', [id])
        cur.execute('DROP TABLE %s' % id)
        mysql.connection.commit()
        cur.close()
        flash('Form Deleted', 'success')
        return redirect(url_for('view_forms'))
    else:
        flash('Failed to Delete Form', 'danger')
        return redirect(url_for('index'))

# View a specific form
@app.route('/forms/<string:form_id>/')
@is_logged_in
def view_form(form_id):
    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * FROM forms WHERE id = %s AND user = %s', [form_id, session['username']])
    if result > 0:
        form = cur.fetchone()
        cur.execute('SELECT * FROM links WHERE form_id = %s', [form_id])
        links = cur.fetchall()

        cur.execute('SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = \'myinvitemanager\' AND TABLE_NAME = \'%s\'' % form_id)
        headers = get_form_table_headers(cur.fetchall())

        cur.execute('SELECT * FROM %s' % form_id)

        responses = cur.fetchall()

        cur.execute('SELECT * FROM qrhash WHERE form = %s', [form_id])
        hashes = cur.fetchall()

        responses = add_hash_to_user_dictionary(responses, hashes)

        cur.close()
        return render_template('form.html', form=form, links=links, headers=headers, users=responses)
    else:
        flash('Form is Unavailable', 'danger')
        cur.close()
        return redirect(url_for('index'))


@app.route('/delete_response', methods=['POST'])
@is_logged_in
def delete_response():
    user_id = request.args.get('user_id', '')
    form_id = request.args.get('form_id', '')

    cur = mysql.connection.cursor()

    result = cur.execute('SELECT * FROM forms WHERE id = %s AND user = %s', [form_id, session['username']])
    if result > 0:
        cur.execute('DELETE FROM %s WHERE id = %s' % (form_id, '\'' + user_id + '\''))
        cur.execute('DELETE FROM qrhash WHERE user_id = %s', [user_id])
        mysql.connection.commit()
        cur.close()
        flash('Respondent Removed', 'success')
        return redirect(url_for('view_form', form_id=form_id))
    else:
        cur.close()
        abort(404)

# Create a link for a form
@app.route('/create_form_link/<string:form_id>', methods=['GET', 'POST'])
@is_logged_in
def create_form_link(form_id):
    if request.method == 'POST':
        name = request.form['name']
        uses = request.form['uses']
        link_id = uuid.uuid1().hex
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO links(id, name, form_id, user, uses, max_uses) VALUES(%s, %s, %s, %s, 0, %s)', (link_id, name, form_id, session['username'], uses))
        mysql.connection.commit()
        cur.close()
        flash('Link Created Successfully', 'success')
        return redirect(url_for('view_form', form_id=form_id))
    return render_template('create_form_link.html', form_id=form_id)


# Delete a form link
@app.route('/delete_form_link/<string:link_id>', methods=['POST'])
@is_logged_in
def delete_form_link(link_id):
    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * FROM links WHERE id = %s AND user = %s', [link_id, session['username']])
    if result > 0:
        form_id = cur.fetchone()['form_id']
        cur.execute('DELETE FROM links WHERE id = %s AND user = %s', [link_id, session['username']])
        mysql.connection.commit()
        flash('Link Successfully Deleted', 'success')
        cur.close()
        return redirect(url_for('view_form', form_id=form_id))
    else:
        flash('Failure to Delete Link', 'danger')
    return redirect(url_for('index'))


# Form gets submitted here
@app.route('/submit_form', methods=['GET', 'POST'])
def submit_form():
    link_id = request.args.get('id', '')

    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * FROM links WHERE id = %s', [link_id])
    if result > 0:
        data = cur.fetchone()
        form_id = data['form_id']
        cur.execute('SELECT * FROM forms WHERE id = %s', [form_id])
        form_data = cur.fetchone()

        form_name = form_data['name']

        link_uses = data['uses']
        link_max = data['max_uses']
        form_uses = form_data['uses']
        form_max = form_data['max_uses']

        if (link_uses >= link_max) and link_max != -1:
            cur.close()
            flash('Link exceeds maximum uses', 'danger')
            return redirect(url_for('index'))
        if (form_uses >= form_max) and form_max != -1:
            cur.close()
            flash('Form exceeds maximum uses', 'danger')
            return redirect(url_for('index'))

        form = build_submission_form(SubmitFormForm(request.form), get_options(form_id, mysql))

        if request.method == 'POST' and form.validate():
            form_uses += 1
            link_uses += 1
            cur.execute('UPDATE forms SET uses = %s WHERE id = %s', [form_uses, form_id])
            cur.execute('UPDATE links SET uses = %s WHERE id = %s', [link_uses, link_id])

            statement = build_submission_statement(form_data['data'], form_id)
            form_results = build_submission_list([form.picture, form.name, form.email, form.phone, form.school])
            cur.execute(statement, form_results)
            mysql.connection.commit()
            user_hash = uuid.uuid1().hex
            cur.execute('INSERT INTO qrhash(hash, user_id, form) VALUES(%s, %s, %s)', (user_hash, cur.lastrowid, form_id))
            mysql.connection.commit()
            flash('Form Successfully Submitted', 'success')
            cur.close()
            return redirect(url_for('view_qr', hash=user_hash))
        cur.close()
        return render_template('submit_link.html', form=form, name=form_name)

    else:
        abort(404)

# Respondent gets redirected here with their qr code
@app.route('/view_qr', methods=['GET', 'POST'])
def view_qr():
    hash = request.args.get('hash', '')
    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * from qrhash WHERE hash = %s', [hash])
    cur.close()
    if result > 0:
        img = produce_qr_string(hash)
        return render_template('view_qr.html', img=img)
    else:
        abort(404)

# This is where the qr code leads
@app.route('/view_respondent', methods=['GET', 'POST'])
@is_logged_in
def view_respondent():
    user_hash = request.args.get('hash', '')
    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * FROM qrhash WHERE hash = %s', [user_hash])
    if result > 0:
        qrhash_data = cur.fetchone()
        form_id = qrhash_data['form']
        user_id = qrhash_data['user_id']
        cur.execute('SELECT * FROM %s WHERE id = %s' % (form_id, '\'' + user_id + '\''))
        user = cur.fetchone()
        print(user)
        cur.close()
        return render_template('view_respondent.html', user=user, form_id=form_id)
    else:
        cur.close()
        flash('Invalid QR Code', 'danger')
        return redirect(url_for('index'))

# Register an account
@app.route('/register', methods=['GET', 'POST'])
@is_logged_out
def register():

    if not allow_registration:
        flash('Registration Disabled', 'danger')
        return redirect(url_for('index'))

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
        cur.execute('INSERT INTO users(name, email, username, password, access_level) VALUES(%s, %s, %s, %s, 0)', (name, email, username, password))
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
                session['username'] = data['username']
                session['access_level'] = data['access_level']
                flash('You are now logged in, '+session['username'], 'success')
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
    cur.execute('DELETE FROM links WHERE user = %s', [session['username']])
    cur.execute('SELECT * FROM forms WHERE user = %s', [session['username']])
    forms = cur.fetchall()
    for form in forms:
        cur.execute('DELETE FROM qrhash WHERE form = %s', [form['id']])
        cur.execute('DROP TABLE %s' % form['id'])
    cur.execute('DELETE FROM forms WHERE user = %s', [session['username']])
    cur.execute('DELETE FROM users WHERE username = %s', [session['username']])
    mysql.connection.commit()
    session.clear()
    flash('Account Successfully Deleted', 'success')
    cur.close()
    return redirect(url_for('index'))


@app.before_first_request
def check_if_tables_exists():
    session.permanent = True
    cur = mysql.connection.cursor()
    result = cur.execute('SHOW TABLES LIKE \'users\'')
    if result < 1:
        print('Creating User Table...')
        cur.execute('CREATE TABLE users(id INT(12) AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), email VARCHAR(100), username VARCHAR(30), password VARCHAR(100), access_level INT(5))')
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
    result = cur.execute('SHOW TABLES LIKE \'links\'')
    if result < 1:
        print('Creating Links Table...')
        cur.execute('CREATE TABLE links(id VARCHAR(50) PRIMARY KEY, name VARCHAR(50), form_id VARCHAR(50), user VARCHAR(30), uses INT(10), max_uses INT(10))')
        mysql.connection.commit()
    else:
        print('Loading Links Table...')
    result = cur.execute('SHOW TABLES LIKE \'qrhash\'')
    if result < 1:
        print('Creating QR Hash Table...')
        cur.execute('CREATE TABLE qrhash(hash VARCHAR(200) PRIMARY KEY, user_id VARCHAR(100), form VARCHAR(50))')
        mysql.connection.commit()
    else:
        print('Loading QR Hash Table...')
    cur.close()


@app.errorhandler(404)
def handle_404(e):
    flash('Page is unauthorized or doesn\'t exist. Check spelling or try again', 'danger')
    return redirect(url_for('index'))


@app.errorhandler(405)
def handle_405(e):
    flash('Page is unauthorized or doesn\'t exist. Check spelling or try again', 'danger')
    return redirect(url_for('index'))


if __name__ == '__main__':
    if show_help:
        show_usage()

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
    QRcode(app)
    app.run(debug=debug_enabled)
else:
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
    QRcode(app)
