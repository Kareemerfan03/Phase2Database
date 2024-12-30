from flask import Flask, render_template, request, session, redirect, url_for
import psycopg2
import os
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
import random




app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'

# Database connection
database_session = psycopg2.connect(
    database='user_info', user='postgres', password='kareem', host='localhost', port='5432'
)

# File upload settings
DOCTOR_UPLOAD_FOLDER = 'static/uploads'
PATIENT_UPLOAD_FOLDER = 'static/uploads'
UPLOAD_FOLDER = 'static/uploads/documents'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(DOCTOR_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PATIENT_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['DOCTOR_UPLOAD_FOLDER'] = DOCTOR_UPLOAD_FOLDER
app.config['PATIENT_UPLOAD_FOLDER'] = PATIENT_UPLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

# @app.route('/')
# def home():
#     return redirect(url_for('admin_view_appointments'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form['email']
    password = request.form['password']
    user_type = request.form.get('user_type')

    if email == 'admin@gmail.com' and password == '111':
        return render_template('admin.html')


    cur = database_session.cursor()
    userdata = None

    if user_type == 'patient':
        cur.execute('SELECT * FROM Patients WHERE email=%s AND password=%s', (email, password))
        userdata = cur.fetchone()
    elif user_type == 'doctor':
        cur.execute('SELECT * FROM Doctors WHERE email=%s AND password=%s', (email, password))
        userdata = cur.fetchone()


    cur.close()

    if userdata is None:
        message = 'Invalid email, password, or user type. Please try again.'
        return render_template('login.html', message=message)

    session['userdata'] = userdata
    session['user_type'] = user_type

    if user_type == 'patient':
        return redirect('/patient_profile')
    elif user_type == 'doctor':
        return redirect('/doctor_profile')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    name = request.form['name']
    dob = request.form['dob']
    gender = request.form['gender']
    phone = request.form['phone']
    blood_group = request.form['blood_group']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    user_type = request.form['user_type']
    valid_blood_groups = {'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'}

    if password != confirm_password:
        message = 'Passwords must match'
    elif blood_group not in valid_blood_groups:
        message = 'Invalid blood group'
    else:
        cur = database_session.cursor()
        cur.execute('SELECT * FROM Patients WHERE name=%s', (name,))
        patient_exists = cur.fetchone()
        cur.execute('SELECT * FROM Doctors WHERE name=%s', (name,))
        doctor_exists = cur.fetchone()

        if patient_exists or doctor_exists:
            message = 'Name already exists in the system'
        else:
            PhotoPath = 'static/uploads/default.png'
            if user_type == 'Patient':
                cur.execute(
                    'INSERT INTO Patients (Name, DateOfBirth, Gender, PhoneNumber, BloodGroup, Email, Password, PhotoPath) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)',
                    (name, dob, gender, phone, blood_group, email, password, PhotoPath))
            elif user_type == 'Doctor':
                cur.execute(
                    'INSERT INTO Doctors (Name, DateOfBirth, Gender, PhoneNumber, BloodGroup, Email, Password, PhotoPath) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)',
                    (name, dob, gender, phone, blood_group, email, password, PhotoPath))

            database_session.commit()
            message = 'Successfully registered!'

        cur.close()
    return render_template('register.html', message=message)

@app.route('/logout')
def logout():
    session.pop('userdata', None)
    session.pop('user_type', None)
    return redirect('/')

@app.route('/patient_profile', methods=['GET', 'POST'])
def patient_profile():
    userdata = session.get('userdata')
    if not userdata or session.get('user_type') != 'patient':
        return redirect('/')

    user_name = userdata[1]

    if request.method == 'POST':
        phone = request.form['phone']
        dob = request.form['dob']
        name = request.form['name']

        cur = database_session.cursor()
        cur.execute('UPDATE Patients SET PhoneNumber=%s, DateOfBirth=%s, Name=%s WHERE Name=%s',
                    (phone, dob, name, user_name))
        database_session.commit()
        cur.close()
        session['userdata'] = (userdata[0], name, userdata[2], phone, userdata[4], dob, userdata[6])

    cur = database_session.cursor()
    cur.execute('SELECT Name, Email, PhoneNumber, BloodGroup, DateOfBirth FROM Patients WHERE name=%s', (user_name,))
    patient_info = cur.fetchone()
    cur.close()

    return render_template('patient_profile.html', info=userdata)
@app.route('/doctor_profile', methods=['GET', 'POST'])
def doctor_profile():
    userdata = session.get('userdata')
    if not userdata or session.get('user_type') != 'doctor':
        return redirect('/')

    user_name = userdata[1]

    if request.method == 'POST':
        phone = request.form['phone']
        blood_group = request.form['blood_group']
        email = request.form['email']

        cur = database_session.cursor()
        cur.execute('UPDATE Doctors SET PhoneNumber=%s, BloodGroup=%s, Email=%s WHERE Name=%s',
                    (phone, blood_group, email, user_name))
        database_session.commit()
        cur.close()
        session['userdata'] = (userdata[0], user_name, userdata[2], phone, blood_group, email, userdata[6])

    cur = database_session.cursor()
    cur.execute('SELECT Name, Email, PhoneNumber, BloodGroup, Gender FROM Doctors WHERE name=%s', (user_name,))
    doctor_info = cur.fetchone()
    cur.close()

    return render_template('doctor_profile.html', info=userdata)

@app.route('/upload_photo/doctor', methods=['POST'])
def upload_doctor_photo():
    userdata = session.get('userdata')
    if not userdata or session.get('user_type') != 'doctor':
        return redirect('/')

    file = request.files['photo']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        doctor_upload_path = os.path.join(app.config['DOCTOR_UPLOAD_FOLDER'],'doctor_upload')
        os.makedirs(doctor_upload_path, exist_ok=True)
        file_path = os.path.join(doctor_upload_path, filename)
        file.save(file_path)

        cur = database_session.cursor()
        cur.execute('UPDATE Doctors SET PhotoPath=%s WHERE Name=%s', (f'/uploads/doctor_upload/{filename}', userdata[1]))
        database_session.commit()
        cur.close()

        userdata = list(userdata)
        userdata[8] = f'doctor_upload/{filename}'
        session['userdata'] = tuple(userdata)

    return redirect('/doctor_profile')


@app.route('/upload_photo/patient', methods=['POST'])
def upload_patient_photo():
    userdata = session.get('userdata')
    if not userdata or session.get('user_type') != 'patient':
        return redirect('/')

    file = request.files['photo']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        patient_upload_path = os.path.join(app.config['PATIENT_UPLOAD_FOLDER'], 'patient_upload')
        os.makedirs(patient_upload_path, exist_ok=True)
        file_path = os.path.join(patient_upload_path, filename)
        file.save(file_path)

        # Update the photo path in the database
        cur = database_session.cursor()
        cur.execute('UPDATE Patients SET PhotoPath=%s WHERE Name=%s', (f'/uploads/patient_upload/{filename}', userdata[1]))
        database_session.commit()
        cur.close()

        # Update session data
        userdata = list(userdata)
        userdata[8] = f'patient_upload/{filename}'  # Assuming index 8 is for photo path
        session['userdata'] = tuple(userdata)

    return redirect('/patient_profile')


@app.route('/pendingappointments', methods=['GET', 'POST'])
def appointment():
    if request.method == 'POST':
        try:
            full_name = request.form['fullname']
            email = request.form['email']
            phone_number = request.form['phonenumber']
            surgery_type = request.form['surgerytype']
            appointment_date = request.form['appointmentdate']
            appointment_time = request.form['appointmenttime']
            concerns = request.form['concerns']
            assigned_doctor = request.form['assigneddoctor']

            cur = database_session.cursor()

            # Check if the patient already has an appointment for the same surgery type
            cur.execute(
                'SELECT * FROM pendingappointments WHERE FullName=%s AND SurgeryType=%s',
                (full_name, surgery_type)
            )
            existing_surgery_appointment = cur.fetchone()
            if existing_surgery_appointment:
                cur.close()
                message = 'Error: You already have a reservation for this type of surgery.'
                return render_template('index.html', message=message)

            # Check if an appointment already exists for the selected date and time
            cur.execute(
                'SELECT * FROM pendingappointments WHERE AppointmentDate=%s AND AppointmentTime=%s',
                (appointment_date, appointment_time)
            )
            existing_appointment = cur.fetchone()
            print(f"Checking existing appointment for {appointment_date} and {appointment_time}: {existing_appointment}")

            if existing_appointment:
                cur.close()
                message = 'An appointment already exists for the selected date and time. Please choose a different time.'
                return render_template('index.html', message=message)

            cur.execute(
                'SELECT * FROM pendingappointments WHERE Email=%s',
                (email,)
            )
            existing_email_appointment = cur.fetchone()

            if existing_email_appointment:
                cur.close()
                message = 'An appointment already exists for you'
                return render_template('index.html', message=message)

            # insert new appointment
            cur.execute(
                'INSERT INTO pendingappointments (FullName, Email, PhoneNumber, SurgeryType, AppointmentDate, AppointmentTime, Concerns, AssignedDoctor) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (full_name, email, phone_number, surgery_type, appointment_date, appointment_time, concerns, assigned_doctor)
            )
            database_session.commit()
            cur.close()

            message = 'You successfully made an appointment.'
            return render_template('index.html', message=message)
        except Exception as e:
            print(f"An error occurred: {e}")
            message = 'An error occurred while processing your request. Please try again later.'
            return render_template('index.html', message=message)

    # Fetch doctor names for the dropdown
    cur = database_session.cur()
    cur.execute('SELECT name FROM doctornames')
    doctors = cur.fetchall()
    cur.close()

    return render_template('index.html', doctors=doctors)



from datetime import datetime

@app.route('/upload_document', methods=['POST'])
def upload_document():
    email = request.form['email']
    file = request.files['file']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'])
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        upload_time = datetime.now().strftime('%d-%m-%Y %I:%M %p')

        cur = database_session.cursor()
        cur.execute('''
            INSERT INTO file_uploads (email, doc_file_path, upload_time)
            VALUES (%s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET doc_file_path = EXCLUDED.doc_file_path, upload_time = EXCLUDED.upload_time
        ''', (email, file_path, upload_time))
        database_session.commit()
        cur.close()

        message = 'File successfully uploaded.'
    else:
        message = 'Invalid file type.'

    userdata = session.get('userdata')
    cur = database_session.cursor()
    cur.execute('SELECT Name, Email, PhoneNumber, BloodGroup, DateOfBirth FROM Patients WHERE name=%s',
                (userdata[1],))
    patient_info = cur.fetchone()
    cur.close()

    return render_template('patient_profile.html', info=patient_info, upload_message=message)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        try:
            cur = database_session.cursor()
            cur.execute('INSERT INTO contact_messages (name, email, message) VALUES (%s, %s, %s)'
                        , (name, email, message))
            database_session.commit()
            cur.close()
            feedback = 'Message sent successfully!'
        except Exception as e:
            print(f"An error occurred: {e}")
            feedback = 'An error occurred while sending your message. Please try again later.'

        return render_template('index.html', feedback=feedback)

    return render_template('index.html')

@app.route('/view_appointments', methods=['GET'])
def view_appointments():
    try:
        cur = database_session.cursor()
        cur.execute('SELECT fullname, email, phonenumber, surgerytype, appointmentdate, appointmenttime, concerns, assigneddoctor FROM pendingappointments')
        appointments = cur.fetchall()
        cur.close()
        return render_template('Appointments.html', appointments=appointments)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('Appointments.html', error=str(e))

@app.route('/filter_appointments', methods=['POST'])
def filter_appointments():
    name = request.form['name']
    try:
        cur = database_session.cursor()
        cur.execute('SELECT fullname, email, phonenumber, surgerytype, appointmentdate, appointmenttime, concerns, assigneddoctor FROM pendingappointments WHERE assigneddoctor=%s', (name,))
        appointments = cur.fetchall()
        cur.close()
        return render_template('Appointments.html', appointments=appointments)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('Appointments.html', error=str(e))

@app.context_processor
def inject_random():
    return {'random': lambda: random.randint(1, 100000)}


@app.route('/approve_appointment', methods=['POST'])
def approve_appointment():
    fullname = request.form['fullname']
    email = request.form['email']
    phonenumber = request.form['phonenumber']
    surgerytype = request.form['surgerytype']
    appointmentdate = request.form['appointmentdate']
    appointmenttime = request.form['appointmenttime']
    try:
        cur = database_session.cursor()
        # Copy the appointment to the realappointments table
        cur.execute('''
            INSERT INTO realappointments (fullname, email, phonenumber, surgerytype, appointmentdate, appointmenttime, concerns, assigneddoctor)
            SELECT fullname, email, phonenumber, surgerytype, appointmentdate, appointmenttime, concerns, assigneddoctor
            FROM pendingappointments
            WHERE fullname = %s AND email = %s AND phonenumber = %s AND surgerytype = %s AND appointmentdate = %s AND appointmenttime = %s
        ''', (fullname, email, phonenumber, surgerytype, appointmentdate, appointmenttime))

        # Delete the appointment from the pendingappointments table
        cur.execute('''
            DELETE FROM pendingappointments
            WHERE fullname = %s AND email = %s AND phonenumber = %s AND surgerytype = %s AND appointmentdate = %s AND appointmenttime = %s
        ''', (fullname, email, phonenumber, surgerytype, appointmentdate, appointmenttime))
        database_session.commit()
        cur.close()
        return redirect(url_for('view_appointments'))
    except Exception as e:
        print(f"An error occurred: {e}")
        return redirect(url_for('view_appointments', error=str(e)))

@app.route('/deny_appointment', methods=['POST'])
def deny_appointment():
    fullname = request.form['fullname']
    email = request.form['email']
    phonenumber = request.form['phonenumber']
    surgerytype = request.form['surgerytype']
    appointmentdate = request.form['appointmentdate']
    appointmenttime = request.form['appointmenttime']
    try:
        cur = database_session.cursor()
        # Delete the appointment from the pendingappointments table
        cur.execute('''
            DELETE FROM pendingappointments
            WHERE fullname = %s AND email = %s AND phonenumber = %s AND surgerytype = %s AND appointmentdate = %s AND appointmenttime = %s
        ''', (fullname, email, phonenumber, surgerytype, appointmentdate, appointmenttime))
        database_session.commit()
        cur.close()
        return redirect(url_for('view_appointments'))
    except Exception as e:
        print(f"An error occurred: {e}")
        return redirect(url_for('view_appointments', error=str(e)))

@app.route('/view_uploads')
def view_uploads():
    try:
        cur = database_session.cursor()
        cur.execute('SELECT email, doc_file_path, upload_time FROM file_uploads')
        uploads = cur.fetchall()
        cur.close()
        return render_template('view_uploads.html', uploads=uploads)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('view_uploads.html', error=str(e))


#/////////////////////////////// Admin Part///////////////////////////////////////
@app.route('/admin_view_appointments')
def admin_view_appointments():
    try:
        cur = database_session.cursor()
        cur.execute('SELECT * FROM pendingappointments')
        appointments = cur.fetchall()
        cur.close()
        return render_template('adminAppointments.html', appointments=appointments)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('adminAppointments.html', error=str(e))
@app.route('/admin_view_realappointments')
def admin_view_realappointments():
    try:
        cur = database_session.cursor()
        cur.execute('SELECT * FROM realappointments')
        realappointments = cur.fetchall()
        cur.close()
        return render_template('adminRealAppointments.html', realappointments=realappointments)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('adminRealAppointments.html', error=str(e))
@app.route('/admin_view_patients')
def admin_view_patients():
    try:
        cur = database_session.cursor()
        cur.execute('SELECT * FROM patients')
        patients = cur.fetchall()
        cur.close()
        return render_template('adminPatients.html', patients=patients)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('adminPatients.html', error=str(e))

@app.route('/admin_delete_patient', methods=['POST'])
def admin_delete_patient():
    patientid = request.form['patientid']

    try:
        cur = database_session.cursor()
        cur.execute('DELETE FROM patients WHERE patientid = %s', (patientid,))
        database_session.commit()
        cur.close()
        message = 'Patient deleted successfully!'
    except Exception as e:
        print(f"An error occurred: {e}")
        message = 'An error occurred while deleting the patient. Please try again later.'

    return redirect(url_for('admin_view_patients', message=message))

@app.route('/admin_add_patient', methods=['GET', 'POST'])
def admin_add_patient():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        phone = request.form['phone']
        blood_group = request.form['blood_group']
        email = request.form['email']
        password = request.form['password']
        photo_path = 'static/uploads/default.png'  # Default photo path

        try:
            cur = database_session.cursor()
            cur.execute('''
                INSERT INTO patients (Name, DateOfBirth, Gender, PhoneNumber, BloodGroup, Email, Password, PhotoPath)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (name, dob, gender, phone, blood_group, email, password, photo_path))
            database_session.commit()
            cur.close()
            message = 'Patient added successfully!'
        except Exception as e:
            print(f"An error occurred: {e}")
            message = 'An error occurred while adding the patient. Please try again later.'

        return redirect(url_for('admin_view_patients', message=message))

    return render_template('adminPatients.html')

@app.route('/admin_view_doctors')
def admin_view_doctors():
    try:
        cur = database_session.cursor()
        cur.execute('SELECT * FROM doctors')
        doctors = cur.fetchall()
        cur.close()
        return render_template('adminDoctors.html', doctors=doctors)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('adminDoctors.html', error=str(e))
@app.route('/admin_delete_doctor', methods=['POST'])
def admin_delete_doctor():
    doctorid = request.form['doctorid']

    try:
        cur = database_session.cursor()
        cur.execute('DELETE FROM doctors WHERE doctorid = %s', (doctorid,))
        database_session.commit()
        cur.close()
        message = 'Doctor deleted successfully!'
    except Exception as e:
        print(f"An error occurred: {e}")
        message = 'An error occurred while deleting the doctor. Please try again later.'

    return redirect(url_for('admin_view_doctors', message=message))

@app.route('/admin_add_doctor', methods=['GET', 'POST'])
def admin_add_doctor():
    if request.method == 'POST':
        name = request.form['name']
        dob = request.form['dob']
        gender = request.form['gender']
        phone = request.form['phone']
        blood_group = request.form['blood_group']
        email = request.form['email']
        password = request.form['password']
        photo_path = 'static/uploads/default.png'  # Default photo path

        try:
            cur = database_session.cursor()
            cur.execute('''
                INSERT INTO doctors (Name, DateOfBirth, Gender, PhoneNumber, BloodGroup, Email, Password, PhotoPath)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (name, dob, gender, phone, blood_group, email, password, photo_path))
            database_session.commit()
            cur.close()
            message = 'Doctor added successfully!'
        except Exception as e:
            print(f"An error occurred: {e}")
            message = 'An error occurred while adding the doctor. Please try again later.'

        return redirect(url_for('admin_view_doctors', message=message))

    return render_template('adminDoctors.html')


@app.route('/admin_view_data')
def admin_view_data():
    try:
        cur = database_session.cursor()
        cur.execute('SELECT email, doc_file_path, upload_time FROM file_uploads')
        data_uploads = cur.fetchall()
        cur.close()
        return render_template('adminDocuments.html', data_uploads=data_uploads)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('adminDocuments.html', error=str(e))


@app.route('/admin_view_messages')
def admin_view_messages():
    try:
        cur = database_session.cursor()
        cur.execute('SELECT * FROM contact_messages')
        messages = cur.fetchall()
        cur.close()
        return render_template('adminMessages.html', messages=messages)
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('adminMessages.html', error=str(e))



if __name__ == '__main__':
    app.run(debug=True)
