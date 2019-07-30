# Form data holds true-false data in this format: picture, name, email, phone #, School
def gen_options(option_list):
    default = ['f', 'f', 'f', 'f', 'f']
    for option in option_list:
        default[option-1] = 't'
    return "".join(default)

