import sys, getopt
from flask import request


# Produces qrcode
def produce_qr_string(data):
    string = 'http://'+request.host + '/view_respondent?hash=' + data
    return string


# Form data holds true-false data in this format: picture, name, email, phone #, School
def gen_options(option_list):
    default = ['f', 'f', 'f', 'f', 'f']
    for option in option_list:
        default[option-1] = 't'
    return "".join(default)


# Grabs the form options and returns it as a string
def get_options(form_id, mysql):
    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * FROM forms WHERE id = %s', [form_id])
    if result > 0:
        data = cur.fetchone()['data']
        cur.close()
        return data
    cur.close()
    return None


# Returns the SQL statement for creating the responder table for a form
# TODO: Fix the bug here somewhere
def create_form_table(options, form_id):
    statement = 'CREATE TABLE ' + str(form_id) + '(id INT(12) AUTO_INCREMENT PRIMARY KEY'
    opts = {0: 'picture', 1: 'name', 2: 'email', 3: 'phone', 4: 'school'}
    iterator = 0
    for elem in options:
        if elem == 't':
            statement += (', ' + opts[iterator] + ' VARCHAR(200)')
        iterator += 1
    statement += ')'
    return statement


# Builds the SQL part of the insertion into the responder database
def build_submission_statement(options, form_id):
    opts = {0: 'picture', 1: 'name', 2: 'email', 3: 'phone', 4: 'school'}
    statement = 'INSERT INTO ' + form_id + '('
    iterator = 0
    for option in options:
        if option == 't':
            statement += (opts[iterator] + ', ')
        iterator += 1
    statement = statement[:-2] + ') VALUES('
    for option in options:
        if option == 't':
            statement += '%s, '
    statement = statement[:-2] + ')'
    return statement


# Grabs the column heads of a responder table
def get_form_table_headers(response):
    res = []
    for col in response:
        res.append(col['COLUMN_NAME'])
    return res


# Returns a list of form data pieces from a submission form
def build_submission_list(results):
    results = list(filter(None.__ne__, results))
    results = list(map(lambda x: x.data, results))
    return results


# Removes unnecessary pieces from a submission form
def build_submission_form(form, options):
    form_elements = {0: 'picture', 1: 'name', 2: 'email', 3: 'phone', 4: 'school'}
    iterator = 0
    for char in options:
        if char == 'f':
            delattr(form, form_elements[iterator])
        iterator += 1
    return form


def add_hash_to_user_dictionary(users, hashes):
    hash_list = {}
    for user_hash in hashes:
        hash_list[user_hash['user_id']] = user_hash['hash']
    for user in users:
        user_id = str(user['id'])
        user['hash'] = hash_list[user_id]
    return users


# Confirms that a username is unique
def check_username(username, mysql):
    cur = mysql.connection.cursor()

    result = cur.execute('SELECT * FROM users WHERE username = %s', [username])
    cur.close()

    if result > 0:
        return False
    else:
        return True


# Confirms that an email is unique
def check_email(email, mysql):
    cur = mysql.connection.cursor()

    result = cur.execute('SELECT * FROM users WHERE email = %s', [email])
    cur.close()

    if result > 0:
        return False
    else:
        return True


# Combined method for convenience (and code golf)
def check_unique_user(username, email, mysql):
    return check_username(username, mysql) and check_email(email, mysql)


def show_usage():
    print('python3 app.py [-d] [-r] [-h]\n[-d][--debug]: Debug Mode\n[-r][--register]: Enable User Registration\n[-h][--help]: Show Usage')
    sys.exit(0)

# Handles command-line arguments
def handle_args():
    res = [False, False, False]

    args = sys.argv[1:]

    unix_options = 'drh'
    gnu_options = ['debug', 'registration', 'help']

    try:
        arguments, values = getopt.getopt(args, unix_options, gnu_options)
    except getopt.error as err:
        print(str(err))
        sys.exit(2)

    for argument, value in arguments:
        if argument in ('-d', '--debug'):
            res[0] = True
        elif argument in ('-r', '--register'):
            res[1] = True
        elif argument in ('-h', '--help'):
            res[2] = True

    return res
