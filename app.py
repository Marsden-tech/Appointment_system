from flask import Flask, render_template, request,redirect,url_for,session,flash
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Sequence, func
import os



app = Flask(__name__, static_folder='static')
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Marsden2001@localhost:5432/Tiba'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecretkey'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'tibasystemkenya@gmail.com'
app.config['MAIL_PASSWORD'] = 'txbapzyhombpvmql'
mail = Mail(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, Sequence('doctor_id_seq', start=1000, increment=1), primary_key=True)
    firstname = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(80), nullable=False)
    contact = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, Sequence('doctor_id_seq', start=10000, increment=2), primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(30), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(80), nullable=False)
    contact = db.Column(db.String(255), nullable=False)
    speciality = db.Column(db.String(100), nullable=False)
    clinic = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    workingdays = db.Column(db.String(100), nullable=False)
    workinghours = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, Sequence('app_id_seq', start=1, increment=1), primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    patient = db.relationship('Patient', backref='appointments')
    doctor = db.relationship('Doctor', backref='appointments')
    appointment_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(80), default='pending')
    created_at = db.Column(db.Date, server_default=func.now())

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, Sequence('adm_id_seq', start=10000, increment=2), primary_key=True)
    firstname = db.Column(db.String(80), nullable=False)
    lastname = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    


db.create_all()

@app.route("/")
def index():
    return render_template('base.html')

@app.route("/doctor-Login", methods=['GET','POST'])
def doctor_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        doctor = Doctor.query.filter_by(username=username).first()
        if doctor is None:
            error = 'Invalid username or password'
        elif doctor.password != password:
            error = 'Invalid username or password'
        else:
            session['doctor_id'] = doctor.id
            session['doctor_name'] = doctor.firstname
            flash('You have been logged in!')
            return redirect(url_for('doctor_appointments'))
    return render_template('doctor_login.html',error=error)

@app.route("/doctor-home")
def doctor_home():
    if 'doctor_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('doctor_login.html',error=error_message)
    doctor_name = session.get('doctor_name')
    return render_template('doctor_home.html', docname=doctor_name)

@app.route("/doctor-appointments", methods=['GET','POST'])
def doctor_appointments():
    if 'doctor_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('doctor_login.html',error=error_message)
    doctor_name = session.get('doctor_name')
    id = session.get('doctor_id')
    rows = db.session.query(Patient.firstname, Patient.lastname, Patient.email, Patient.address, Patient.contact, Appointment.created_at, Appointment.appointment_date, Appointment.id).join(Appointment).filter(Appointment.doctor_id==id, Appointment.status=='pending')
    return render_template('doctor_appointments.html', docname=doctor_name, rows=rows)

@app.route("/approve-appointment/<int:id>", methods=['POST'])
def approve_appointment(id):
    if 'doctor_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('doctor_login.html',error=error_message)
    
    docname =session.get('doctor_name')
    docid = session.get('doctor_id')
    doc_details = Doctor.query.filter_by(id=docid).first()
    doclname = doc_details.lastname
    doc_email = doc_details.email
    apptmt = Appointment.query.get_or_404(id)
    app_date = apptmt.appointment_date
    pat_id = apptmt.patient_id
    pat_details = Patient.query.filter_by(id=pat_id).first()
    pat_email = pat_details.email
    username = pat_details.firstname
    patlname = pat_details.lastname
    pat_gender = pat_details.gender
    apptmt.status = 'approved'
    db.session.commit()

    msg1 = Message('Appointment Request Approval', sender='tibasystemkenya@gmail.com', recipients=[doc_email])
    msg1.body = f"Hi Dr. {docname} {doclname}, your have successfully approved an appointment request from Mr./Mrs {username} {patlname} for the date {app_date}. Thank you for choosing Tiba."

    msg = Message('Appointment Request Approval', sender='tibasystemkenya@gmail.com', recipients=[pat_email])
    msg.body = f"Hi {username}, your appointment request for {app_date} with Dr {docname} {doclname}  has successfully been approved. Thank you for choosing us."

    mail.send(msg1)
    mail.send(msg)
    return redirect(url_for('doctor_appointments'))

@app.route("/decline-appointment/<int:id>", methods=['POST'])
def decline_appointment(id):
    if 'doctor_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('doctor_login.html',error=error_message)
    apptmt = Appointment.query.get_or_404(id)
    db.session.delete(apptmt)
    db.session.commit()
    return redirect(url_for('doctor_appointments'))


@app.route("/doctor-approved-appointments")
def doc_approved_appointments():
    if 'doctor_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('doctor_login.html',error=error_message)
    doctor_name = session.get('doctor_name')
    id = session.get('doctor_id')
    rows = db.session.query(Patient.firstname, Patient.lastname, Patient.email, Patient.address, Patient.contact, Appointment.created_at, Appointment.appointment_date, Appointment.id).join(Appointment).filter(Appointment.doctor_id==id, Appointment.status=='approved')
    return render_template('doc_approved.html',docname=doctor_name,rows=rows)

@app.route("/close-appointment/<int:id>", methods=['POST'])
def close_appointment(id):
    if 'doctor_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('doctor_login.html',error=error_message)
    apptmt = Appointment.query.get_or_404(id)
    apptmt.status = 'completed'
    db.session.commit()
    return redirect(url_for('doc_approved_appointments'))

@app.route("/appointment-history")
def apptmt_history():
    if 'doctor_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('doctor_login.html',error=error_message)
    doctor_name = session.get('doctor_name')
    id = session.get('doctor_id')
    rows = db.session.query(Patient.firstname, Patient.lastname, Patient.email, Patient.address, Patient.contact, Appointment.created_at, Appointment.appointment_date, Appointment.id).join(Appointment).filter(Appointment.doctor_id==id, Appointment.status=='completed')
    return render_template('doc_apptmt_history.html', docname=doctor_name, rows=rows)

@app.route("/edit-doctor", methods=['GET','POST'])
def edit_doctor():
    if 'doctor_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('doctor_login.html',error=error_message)
    doctor_name = session.get('doctor_name')
    id = session.get('doctor_id')
    item = Doctor.query.get_or_404(id)
    if request.method == 'POST':
        item.firstname = request.form['firstname']
        item.lastname = request.form['lastname']
        item.dob = request.form['DOB']
        item.email = request.form['emailaddress']
        item.contact = request.form['contact']
        item.speciality = request.form['speciality']
        item.clinic = request.form['cname']
        item.location = request.form['cloc']
        item.workingdays = request.form['wdays']
        item.workinghours = request.form['whours']

        db.session.commit()
        return redirect(url_for('doctor_appointments'))
    return render_template('edit_doctor.html',docname=doctor_name, item=item)

@app.route("/patient-Login", methods=['GET','POST'])
def patient_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Patient.query.filter_by(username=username).first()
        if user is None:
            error = 'Invalid username or password'
        elif user.password != password:
            error = 'Invalid username or password'
        else:
            session['user_id'] = user.id
            session['user_name'] = user.firstname
            flash('you have been logged in!')
            return redirect(url_for('view_doctors'))
    return render_template('patient_login.html',error=error)

@app.route("/patient-home")
def patient_home():
    username= session.get('user_name')
    id = session.get('user_id')
    return render_template('patient_home.html',username=username,id=id)

@app.route("/edit-patient", methods=['GET','POST'])
def edit_patient():
    if 'user_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('patient_login.html',error=error_message)
    id = session.get('user_id')
    username = session.get('user_name')
    item = Patient.query.get_or_404(id)
    if request.method == 'POST':
        item.firstname = request.form['firstname']
        item.lastname = request.form['lastname']
        item.dob = request.form['DOB']
        item.email = request.form['emailaddress']
        item.contact = request.form['contact']
        item.address = request.form['address']

        db.session.commit()
        return redirect(url_for('view_doctors'))
    return render_template('edit_patient.html',item=item, username=username)


@app.route("/view-doctor")
def view_doctors():
    user_name = session.get('user_name')
    data = Doctor.query.all()
    return render_template('request_appointment.html',data=data,username=user_name)

@app.route("/add-appointment/<int:doc_id>", methods = ['GET', 'POST'])
def add_appointment(doc_id):
    if 'user_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('patient_login.html',error=error_message)
    username = session.get('user_name')
    patient = session.get('user_id')
    item = Doctor.query.get_or_404(doc_id)
    doc = item.id
    docname = item.firstname
    doclname = item.lastname
    if request.method == 'POST':
        app_date = request.form.get('date')
        appt = Appointment(patient_id=patient, doctor_id=doc, appointment_date=app_date)
        db.session.add(appt)
        db.session.commit()

        doc_email = item.email
        patd = Patient.query.filter_by(id=patient).first()
        pat_email = patd.email
        pat_lname = patd.lastname
        pat_gender = patd.gender

        msg1 = Message('Appointment Request', sender='tibasystemkenya@gmail.com', recipients=[doc_email])
        msg1.body = f"Hi {docname}, You have received an appointment request from Mr./Mrs. {username} {pat_lname} for the date {app_date}. Log in to the website to approve or decline the request. Thank you for being with us."
        

        msg = Message('Appointment Request Confirmation', sender='tibasystemkenya@gmail.com', recipients=[pat_email])
        msg.body = f"Hi {username}, your appointment request for {app_date} with Dr {docname} {doclname}  has successfully been received awaiting approval. Thank you for choosing us."
        
        mail.send(msg1)
        mail.send(msg)
        return redirect(url_for('view_doctors'))
    return render_template('add_appointment.html',item=item, patient=patient, username=username)

@app.route("/pending-appointments")
def pending_appointments():
    if 'user_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('patient_login.html',error=error_message)
    username = session.get('user_name')
    patient = session.get('user_id')
    rows = db.session.query(Doctor.firstname, Doctor.lastname, Doctor.clinic, Doctor.location, Appointment.created_at, Appointment.appointment_date).join(Appointment).filter(Appointment.patient_id==patient, Appointment.status=='pending')

    return render_template('pending_appointments.html',rows=rows, username=username)

@app.route("/approved-appointments")
def approved_appointments():
    if 'user_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('patient_login.html',error=error_message)
    username = session.get('user_name')
    patient = session.get('user_id')

    rows = db.session.query(Doctor.firstname, Doctor.lastname, Doctor.clinic, Doctor.location, Doctor.email, Doctor.contact, Appointment.created_at, Appointment.appointment_date).join(Appointment).filter(Appointment.patient_id==patient, Appointment.status=='approved')

    return render_template('approved_appointments.html',username=username,rows=rows)

@app.route("/previous-appointments")
def previous_appointments():
    if 'user_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('patient_login.html',error=error_message)
    username = session.get('user_name')
    patient = session.get('user_id')

    rows = db.session.query(Doctor.firstname, Doctor.lastname, Doctor.clinic, Doctor.location, Doctor.email, Doctor.contact, Appointment.created_at, Appointment.appointment_date).join(Appointment).filter(Appointment.patient_id==patient, Appointment.status=='completed')

    return render_template('previous_appointments.html',username=username, rows=rows)



@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        dob = request.form['DOB']
        gender = request.form['Gender']
        email = request.form['emailaddress']
        contact = request.form['contact']
        homeaddress = request.form['address']
        username = request.form['username']
        password = request.form['password']
        cpass = request.form['cpassword']

        if password == cpass:
            patient = Patient.query.filter_by(username=username).first()
            if patient:
                return redirect(url_for('signup'))
            new_pat = Patient(firstname=firstname, lastname=lastname, dob=dob, gender=gender, email=email, contact=contact, address=homeaddress, username=username, password=password)

            db.session.add(new_pat)
            db.session.commit()
            return redirect(url_for('patient_login'))

    return render_template('signup.html')

@app.route("/admin-login", methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin is None:
            error = 'Invalid username or password'
        elif admin.password != password:
            error = 'Invalid username or password'
        else:
            session['admin_id'] = admin.id
            session['admin_name'] = admin.firstname
            flash('you have been logged in!')
            return redirect(url_for('new_doctor'))

    return render_template('admin_login.html', error=error)



@app.route("/admin-home")
def admin_home():
    if 'admin_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('admin_login.html',error=error_message)
    
    admin_name = session.get('admin_name')
    admin_id = session.get('admin_id')
    if not admin_name:
        return redirect(url_for('admin_login'))
    return render_template('admin_home.html',admin_name=admin_name, admin_id=admin_id)

@app.route("/new-doctor", methods=['GET','POST'])
def new_doctor():
    if 'admin_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('admin_login.html',error=error_message)
    admin_name = session.get('admin_name')
    if request.method == 'POST':
        fname = request.form['firstname']
        lname = request.form['lastname']
        gender = request.form['Gender']
        dob = request.form['DOB']
        email = request.form['emailaddress']
        contact = request.form['contact']
        speciality = request.form['speciality']
        cname = request.form['cname']
        cloc = request.form['cloc']
        wdays = request.form['wdays']
        whours = request.form['whours']
        username = request.form['username']
        password = request.form['password']

        doc = Doctor.query.filter_by(username=username).first()
        if doc:
            return render_template('new_doctor.html')


        doctor = Doctor(firstname=fname, lastname=lname, gender=gender, dob=dob, email=email, contact=contact, speciality=speciality,   clinic=cname, location=cloc, workingdays=wdays, workinghours=whours, username=username, password=password)
        db.session.add(doctor)
        db.session.commit()
        return redirect(url_for('new_doctor'))
    return render_template('new_doctor.html',admin_name=admin_name)

@app.route("/view-doctors")
def view_doctor():
    if 'admin_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('admin_login.html',error=error_message)
    admin_name = session.get('admin_name')
    data = Doctor.query.all()
    return render_template('view_doctor.html',data=data,admin_name=admin_name)

@app.route("/edit_item/<int:id>", methods=['GET','POST'])
def edit_doctor_admin(id):
    if 'admin_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('admin_login.html',error=error_message)
    admin_name = session.get('admin_name')
    item = Doctor.query.get_or_404(id)
    if request.method == 'POST':
        item.firstname = request.form['firstname']
        item.lastname = request.form['lastname']
        item.dob = request.form['DOB']
        item.email = request.form['emailaddress']
        item.contact = request.form['contact']
        item.speciality = request.form['speciality']
        item.clinic = request.form['cname']
        item.location = request.form['cloc']
        item.workingdays = request.form['wdays']
        item.workinghours = request.form['whours']

        db.session.commit()
        return redirect(url_for('view_doctor'))

    return render_template('edit_doctor_admin.html', item=item, admin_name=admin_name)

@app.route("/delete_item/<int:id>", methods=['POST'])
def delete_doctor(id):
    if 'admin_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('admin_login.html',error=error_message)
    item = Doctor.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('view_doctor'))


@app.route("/new-admin", methods=['POST','GET'])
def new_admin():
    if 'admin_id' not in session:
        error_message = session.pop('error_message','You must be logged in to access this page!')
        return render_template('admin_login.html',error=error_message)
    admin_name = session.get('admin_name')
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['emailaddress']
        username = request.form['username']
        password = request.form['password']

        adm = Admin.query.filter_by(username=username).first()
        if adm:
            return render_template('new_admin.html')
        new_adm = Admin(firstname=firstname, lastname=lastname, email=email, username=username, password=password)
        db.session.add(new_adm)
        db.session.commit()
        return redirect(url_for('new_admin'))
    return render_template('new_admin.html',admin_name=admin_name)

@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route("/patient-logout")
def patient_logout():
    session.clear()
    return redirect(url_for('patient_login'))

@app.route("/doctor-logout")
def doctor_logout():
    session.clear()
    return redirect(url_for('doctor_login'))

