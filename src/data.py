# Form data holds true-false data in this format: picture, name, email, phone #, School
def gen_options(option_list):
    default = ['f', 'f', 'f', 'f', 'f']
    for option in option_list:
        default[option-1] = 't'
    return "".join(default)


def get_options(form_id, mysql):
    cur = mysql.connection.cursor()
    result = cur.execute('SELECT * FROM forms WHERE id = %s', [form_id])
    if result > 0:
        data = cur.fetchone()['data']
        cur.close()
        return data
    cur.close()
    return None


def build_submission_form(form, options):
    form_elements = {0: 'picture', 1: 'name', 2: 'email', 3: 'phone', 4: 'school'}
    iterator = 0
    for char in options:
        if char == 'f':
            delattr(form, form_elements[iterator])
        iterator += 1
    return form


def check_username(username, mysql):
    cur = mysql.connection.cursor()

    result = cur.execute('SELECT * FROM users WHERE username = %s', [username])
    cur.close()

    if result > 0:
        return False
    else:
        return True


def check_email(email, mysql):
    cur = mysql.connection.cursor()

    result = cur.execute('SELECT * FROM users WHERE email = %s', [email])
    cur.close()

    if result > 0:
        return False
    else:
        return True


def check_unique_user(username, email, mysql):
    return check_username(username, mysql) and check_email(email, mysql)