from flask import Flask, render_template, redirect, url_for, flash, abort, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SubmitField, BooleanField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_bootstrap import Bootstrap
import datetime
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
Bootstrap(app)

@app.errorhandler(Exception)
def handle_exception(error):
    error_code = getattr(error, 'code', 500)
    return render_template('error.html', error_code=error_code), error_code

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return user
    else:
        return None

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password = db.Column(db.String(128))

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    serial = db.Column(db.Integer)
    date = db.Column(db.String(10))
    measurement = db.Column(db.Text)
    runtime = db.Column(db.Integer)
    cost = db.Column(db.String(32))
    inspector = db.Column(db.Text)
    area = db.Column(db.Text)

with app.app_context():
    db.create_all()

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()], render_kw={"class": "form-control"})
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"class": "form-control"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"class": "form-control"})
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')], render_kw={"class": "form-control"})
    submit = SubmitField('Sign Up', render_kw={"class": "btn btn-primary"})

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"class": "form-control"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"class": "form-control"})
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In', render_kw={"class": "btn btn-primary"})

class DeviceForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()], render_kw={"class": "form-control"})
    serial = IntegerField('Serial number', validators=[DataRequired()], render_kw={"class": "form-control"})
    date = DateField('Date of measurement', format='%Y-%m-%d', validators=[DataRequired()], render_kw={"class": "form-control"})
    measurement = TextAreaField('Measurement', validators=[DataRequired()], render_kw={"class": "form-control"})
    runtime = IntegerField('Time of work (hours)', validators=[DataRequired()], render_kw={"class": "form-control"})
    cost = IntegerField('Cost of measurement', validators=[DataRequired()], render_kw={"class": "form-control"})
    inspector = StringField('Inspector', validators=[DataRequired()], render_kw={"class": "form-control"})
    area = StringField('Location of device', validators=[DataRequired()], render_kw={"class": "form-control"})
    submit = SubmitField('Add Device', render_kw={"class": "btn btn-primary mr-2"})

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_by_email, user_by_username = User.query.filter_by(email=form.email.data).first(), User.query.filter_by(username=form.username.data).first()

        if user_by_email or user_by_username:
            flash('Username or email already exists!')
        else:
            user = User(username=form.username.data, email=form.email.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('devices'))
        else:
            flash('Invalid email or password')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/devices', methods=['GET', 'POST'])
@login_required
def devices():
    devices = Device.query.all()
    return render_template('devices.html', devices=devices)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = DeviceForm()
    if form.validate_on_submit():
        device = Device(name=form.name.data, serial=form.serial.data, date=form.date.data, measurement=form.measurement.data, runtime=form.runtime.data, cost=form.cost.data, inspector=form.inspector.data, area=form.area.data)
        db.session.add(device)
        db.session.commit()
        flash('Device has been added successfully!')
        return redirect(url_for('devices'))
    devices = Device.query.all()
    return render_template('add.html', form=form, devices=devices)

@app.route('/edit/<int:device_id>', methods=['GET', 'POST'])
@login_required
def edit(device_id):
    device = Device.query.get_or_404(device_id)
    form = DeviceForm(obj=device)
    if form.validate_on_submit():
        device.name=form.name.data
        device.type=form.serial.data
        device.date=form.date.data
        device.measurement=form.measurement.data
        device.runtime=form.runtime.data
        device.cost=form.cost.data
        device.inspector=form.inspector.data
        device.area=form.area.data
        db.session.commit()
        flash('Device has been updated successfully!')
        return redirect(url_for('devices'))

    form.date.data = datetime.datetime.strptime(form.date.data, '%Y-%m-%d')
    return render_template('edit.html', form=form)

@app.route('/delete/<int:device_id>', methods=['GET', 'POST'])
@login_required
def delete(device_id):
    device = Device.query.get_or_404(device_id)
    db.session.delete(device)
    db.session.commit()
    flash('Device has been deleted successfully!')
    return redirect(url_for('devices'))

@app.route('/report/<int:device_id>', methods=['GET', 'POST'])
@login_required
def report(device_id):
    device = Device.query.get_or_404(device_id)
    c = canvas.Canvas(f'device_№{device.id}_report.pdf')
    c.setFont('Helvetica-Bold', 20)
    c.drawString(100, 750, 'Device Report')
    c.setFont('Helvetica', 12)
    c.drawString(50, 700, f'Identificator: {device.id}')
    c.drawString(50, 680, f'Name: {device.name}')
    c.drawString(50, 660, f'Date of measurement: {device.date}')
    c.drawString(50, 640, f'Measurement: {device.measurement}')
    c.drawString(50, 620, f'Runtime: {device.runtime}')
    c.drawString(50, 600, f'Cost of measurement: {device.cost}')
    c.drawString(50, 580, f'Measurement inspector: {device.inspector}')
    c.drawString(50, 560, f'Device area: {device.area}')

    c.save()

    with open(f'device_№{device.id}_report.pdf', 'rb') as pdf_file:
        response = Response(pdf_file, mimetype='application/pdf')
        response.headers.set('Content-Disposition', 'inline', filename='device_№{device.id}_report.pdf')
        return response

if __name__ == '__main__':
    app.run(debug=True)