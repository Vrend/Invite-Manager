from wtforms import Form, StringField, PasswordField, validators, widgets, SelectMultipleField, IntegerField, FileField


# Registration form
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=3, max=50), validators.email(message="Must be a Valid Email")])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message="Passwords don't match"), validators.Length(min=5, max=50)])
    confirm = PasswordField('Confirm Password', )


# Form Creation Form
class CheckBoxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class FormCreationForm(Form):
    name = StringField('Form Name', [validators.Length(min=1, max=50)])
    options = [(1, 'picture'), (2, 'name'), (3, 'email'), (4, 'Phone #'), (5, 'School')]
    data = CheckBoxField('Field Options', choices=options, coerce=int)
    uses = IntegerField('Form Uses', [validators.DataRequired(message='Give a number, -1 for infinite uses'), validators.NumberRange(min=-1)])


# Form for Form Submission
class SubmitFormForm(Form):
    picture = StringField('Picture (Link hosted)', [validators.url(message='Please enter a valid image URL')])
    name = StringField('Name', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.email()])
    phone = StringField('Phone #', [validators.Regexp('^[2-9]\\d{2}-\\d{3}-\\d{4}$', message="Enter a valid phone number: XXX-XXX-XXXX")])
    school = StringField('School', [validators.DataRequired()])

