import mysql.connector
from mysql.connector import MySQLConnection, Error
from mysql.connector.errors import IntegrityError
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
        print("Authenticating(user,pass): ", format(args))
        cursor.execute(query, args)
        row = cursor.fetchone()
        print("Authentication Query Result:", format(row))

    except Error as error:
        print(error)
        return("Error: {}".format(error))

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
        return redirect(url_for("user"))
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
        conn = connect()
        row = None
        try: 
            cursor = conn.cursor()
            query = "SELECT first_name, last_name, register_date FROM credentials WHERE email = %s"
            args = (session['username'])
            print("Retreiving data for: ", format(args))
            cursor.execute(query, args)
            row = cursor.fetchone()
            print("Authentication Query Result:", format(row))

        except Error as error:
            print(error)
            return("Error: {}".format(error))

        finally:
            cursor.close()
            conn.close()
            print('Connection closed.')
            return render_template('user.html', username=session['username'], row=row)
    else:
        return render_template("login.html", authError="Please log in")

@app.route("/register", methods=['POST', 'GET'])
def register():
    error = ""
    if request.method == 'POST':
        if request.form['password'] != request.form['password_confirm']:
            return render_template('register.html', passwordMismatch = "Passwords do not match", email=request.form['email'], first_name=request.form['first_name'], last_name=request.form['last_name'])
        
        conn = connect()
        try: 
            cursor = conn.cursor()
            query = "INSERT INTO credentials(email,password, first_name, last_name) VALUES(%s,%s,%s,%s)"
            args = (request.form['email'], request.form['password'], request.form['first_name'], request.form['last_name'])
            cursor.execute(query, args)
            print("Attempting to add to table: ", format(args))

            if cursor.lastrowid:
                print("Successfully inserted id: ", cursor.lastrowid)
                conn.commit()
                return("Successfully registered user: {}", request.form['email'])

        except IntegrityError as error:
            print(error)
            return render_template("register.html", error="Username/email already exists. Please login")
        except Error as error:
            print(error)
            return("Error: {}".format(error))

        finally:
            cursor.close()
            conn.close()
            print('Connection closed.')    

    return render_template('register.html')

@app.route("/logout")
def logout():
    session.pop('username',None)
    return redirect(url_for('index'))