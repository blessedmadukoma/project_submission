from werkzeug.utils import secure_filename
import os, smtplib, sqlite3, re, uuid
from flask_mail import Mail, Message
from io import BytesIO
from flask import Flask, render_template, redirect, url_for, flash, session, logging, request, send_file
from flask_mysqldb import MySQL
from forms import RegisterForm, UploadForm, ResetPasswordForm
from passlib.hash import sha256_crypt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from functools import wraps

UPLOAD_FOLDER = 'C:/Users/MADUKOMA BLESSED C/Desktop/Code_With_Friends_Project'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'blessed9999'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'blessed10'
app.config['MYSQL_DB'] = 'codewithfriends'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Init MySQL
mysql = MySQL(app)

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'loggedin' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login or Register', 'danger')
            return redirect(url_for('login'))
    return wrap

# Welcome page
@app.route('/')
def home():
    if 'loggedin' in session:
        flash('Already logged in!', 'warning')
        return redirect(url_for('dashboard'))
    return render_template('home.html')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        if form.validate():
            first_name = form.first_name.data
            last_name = form.last_name.data
            email = form.email.data
            password = sha256_crypt.encrypt(str(form.password.data))
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            account = cursor.fetchone()
            if account:
                flash('Account already exists!', 'danger')
                return redirect(url_for('login'))
            if not re.match('[^@]+@[^@]+\\.[^@]+', email):
                flash('Invalid email address!', 'danger')
            elif not password or not email:
                fash('Please fill out the form!', 'danger')
            else:
                cur = mysql.connection.cursor()
                cur.execute('INSERT INTO users(first_name, last_name, email, password) VALUES(%s, %s, %s, %s)', (first_name, last_name, email, password))
                mysql.connection.commit()
                cur.close()
                flash('Thanks for registering. Log in', 'success')
                return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_candidate = request.form['password']
        cursor = mysql.connection.cursor()
        result = cursor.execute(
            'SELECT * FROM users WHERE email = %s', (email,))
        if result > 0:
            account = cursor.fetchone()
            password = account['password']
            if sha256_crypt.verify(password_candidate, password):
                session['loggedin'] = True
                session['id'] = account['id']
                session['first_name'] = account['first_name']
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard'))
            flash('Wrong Password!', 'danger')
            return redirect(url_for('login'))
            cursor.close()
        else:
            flash('account(email) not found', 'danger')
            return redirect(url_for('register'))
    return render_template('login.html')

# Logout function
@app.route('/logout')
def logout():
    flash('You have logged off successfully', 'success')
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    return redirect(url_for('login'))

# Change Password
@app.route('/change_password', methods=['GET', 'POST'])
@is_logged_in
def change_password():
    if request.method == "POST":
        email = request.form['email']
        old = request.form['oldpassword']
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        if password != confirm_password:
            flash("Password and Confirmed Password do not match!", 'danger')
        password = sha256_crypt.encrypt(str(password))
        cur = mysql.connection.cursor()
        result1 = cur.execute("SELECT * FROM users WHERE email=%s", [email])
        if result1 < 1:
            flash("Email not registered!", "danger")
        data = cur.fetchone()
        passw = data['password']
        cur.execute("UPDATE users SET password=%s WHERE email=%s",
                    [password, email])
        mysql.connection.commit()
        flash("Password successfully updated!", "success")
        return redirect(url_for('dashboard'))
    return render_template('change_password.html')

# forgot password
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'loggedin' in session:
        flash("Already logged in!", "warning")
        return redirect(url_for('change_password'))
    if request.method == "POST":
        email = request.form["email"]
        token = str(uuid.uuid4())
        print(token)
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE email=%s", [email])
        if result > 0:
            data = cur.fetchone()
            msg = MIMEMultipart()
            msg['From'] = "skillzskillz01@gmail.com"
            msg['To'] = email
            msg['Subject'] = "Reset Password"
            body = render_template("sent.html", token=token, data=data)
            msg.attach(MIMEText(body, 'plain'))
            s = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            # s = smtplib.SMTP("smtp.gmail.com", 587)
            # s.ehlo()
            # s.starttls()
            # s.ehlo()
            s.login("skillzskillz01@gmail.com", "MadukomaBlessed9")
            print('logged in')
            text = msg.as_string()
            s.sendmail("skillzskillz01@gmail.com", email, text)
            print('mail sent!')

            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET token=%s WHERE email=%s", [token, email])
            mysql.connection.commit()
            cur.close()
            flash("Check Email for next step!", "success")
            return redirect(url_for('reset_password'))
        else:
            flash("Email not registered!", "danger")
    return render_template('reset_password.html')

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    if 'loggedin' in session:
        return render_template('dashboard.html')
    if request.method == "POST":
        password = request.form['password']
        confirm_pass = request.form['confirm_pass']
        token1 = str(uuid.uuid4())
        if password != confirm_pass:
            flash("The Passwords do not match!", 'danger')
        password = sha256_crypt.encrypt(str(password))
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE token=%s", [token])
        data = cur.fetchone()
        if data:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET token=%s, password=%s WHERE token=%s",[token1, password, token])
            mysql.connection.commit()
            cur.close()
            flash("Password successfully updated!", "success")
            return redirect(url_for('login'))
        else:
            flash("Invalid token!", "danger")
            return redirect(url_for('reset_password'))
    return render_template("reset.html")

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html', first_name=(session['first_name']))

# Allowing file function
def allowed_file(filename):
    return '.' in filename and \
         filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Submit Project
@app.route('/submitproj', methods=['GET', 'POST'])
@is_logged_in
def submitproj():
    form = UploadForm()
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        lectemail = request.form.get('lectemail')
        epassword = request.form['pass']
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            database(first_name=first_name, last_name=last_name,email=email, lectemail=lectemail, file=filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = lectemail
            msg['Subject'] = "Project Submission"
            body = f"{last_name} {first_name} sent an assignment"
            msg.attach(MIMEText(body, 'plain'))
            attachment = open(f"C:\\Users\\MADUKOMA BLESSED C\\Desktop\\Code_With_Friends_Project\\{filename}", "rb")
            p = MIMEBase('application', 'octet-stream')
            p.set_payload((attachment).read())
            encoders.encode_base64(p)
            p.add_header('Content-Disposition',"attachment; filename= %s" % filename)
            msg.attach(p)
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            #server = smtplib.SMTP("smtp.gmail.com", 587)
            #server.ehlo()
            #server.starttls()
            #server.ehlo()
            if not (first_name and last_name and email and lectemail):
                flash('All Form Fields Required..', 'danger')
                return redirect('submittedproj')
            server.login(email, epassword)
            print('Logged in')
            text = msg.as_string()
            server.sendmail(email, lectemail, text)
            print('Email sent!')
        flash('Project submitted!', 'success')
    return render_template('submitproj.html')

# Database function
def database(first_name, last_name, email, lectemail, file):
    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO filetable(first_name, last_name, email, lectemail, file) VALUES(%s, %s, %s, %s, %s)',(first_name, last_name, email, lectemail, file))
    mysql.connection.commit()
    rows = cur.fetchall()
    cur.close()

# Submitted Projects
@app.route('/submittedproj', methods=['GET', 'POST'])
@is_logged_in
def submittedproj():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM filetable")
    rows = cur.fetchall()
    cur.close()
    return render_template('submittedproj.html', rows=rows)

# Delete a row in submitted projects
@app.route("/delete/<string:id>", methods=['POST','GET'])
@is_logged_in
def delete(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM filetable WHERE id=%s", (id,))
    mysql.connection.commit()
    flash("Your row has been deleted", "danger")
    return redirect(url_for('submittedproj'))

if __name__ == '__main__':
    app.run(debug=True)