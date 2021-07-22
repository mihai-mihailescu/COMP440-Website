import mysql.connector
from mysql.connector import MySQLConnection, Error
from project_dbconfig import read_db_config
from flask import Flask


from flask import render_template
from flask import abort, redirect, url_for
from flask import request, session

app = Flask(__name__)
app.secret_key = b'\x93\xf3\xb2x\x81s\xd9.\x856iY\xd6\xf1;\xad'


def connect():
    """ Connect to MySQL database """

    db_config = read_db_config()
    conn = None
    try:
        print('Connecting to MySQL database...')
        conn = MySQLConnection(**db_config)

        if conn.is_connected():
            print('Connection established.')
        else:
            print('Connection failed.')
    ##if database connection failed should show 404 error
    except Error as error:
        print(error)

    return conn

def authorize(user, password):
    conn = connect()
    row = None
    try: 
        cursor = conn.cursor()
        query = "SELECT email FROM credentials WHERE email = %s AND password = %s"
        args = (user, password)
        cursor.execute(query, args)
        row = cursor.fetchone()
        print("Authentication Query Result: ")
        print(row)

    except Error as error:
        print(error)

    finally:
        cursor.close()
        conn.close()
        print('Connection closed.')
    
    return row

@app.route("/")
def index():
    return redirect(url_for("home"))

@app.route("/home")
def home():
    if 'username' in session:
        return render_template('user.html', username=session['username'])
    else:
        return render_template("home.html")

@app.route("/login", methods=['POST', 'GET'])
def login():
    error = ""

    if request.method == 'POST':
        user = authorize(request.form['username'], request.form['password'])
        if user is not None:
            session['username'] = user
            return redirect("/user/"+user[0])
        else:
            error = 'Invalid username/password'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template('login.html', authError=error)


@app.route("/user/")
@app.route("/user/<username>")
def user(username=None):
    if 'username' in session:
        return render_template('user.html', username=session['username'])
    else:
        return redirect(url_for(login))

@app.route("/register", methods=['POST', 'GET'])
def register():
    error = ""
    if request.method == 'POST':
        if request.form['password'] != request.form['password_confirm']:
            return render_template('register.html', passwordMismatch = "Passwords do not match", email=request.form['email'], first_name=request.form['first_name'], last_name=request.form['last_name'])
        return "User registered"

    error = "Field cannot be empty"
    return render_template('register.html')

@app.route("/logout")
def logout():
    session.pop('username',None)
    return redirect(url_for('index'))