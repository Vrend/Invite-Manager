# Form data holds true-false data in this format: picture, name, email, phone #, School
def gen_options(option_list):
    default = ['f', 'f', 'f', 'f', 'f']
    for option in option_list:
        default[option-1] = 't'
    return "".join(default)


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