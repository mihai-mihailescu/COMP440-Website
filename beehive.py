from mysql.connector import MySQLConnection, Error
from mysql.connector.errors import IntegrityError
from project_dbconfig import read_db_config
from flask import Flask

from datetime import date


from flask import render_template
from flask import abort, redirect, url_for
from flask import flash
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
        query = "SELECT username,userid FROM users WHERE username = %s AND password = %s"
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
    ## OLD CODE IS HERE ##
    #if 'username' in session:
    #    return redirect(url_for("user"))
    #else:
    #    return render_template("home.html")
    
    #Before logging in we display all the blogs if any are available
    conn = connect()
    blogs = None

    try:
        cursor = conn.cursor()
        query = "SELECT blogid,subject,description,pdate,username FROM blogs INNER JOIN users ON users.userid = blogs.userid"
        print("Executing query: " + query)
        cursor.execute(query)
        blogs = cursor.fetchall()
        print("Query result: ", len(blogs))

    except Error as error:
        print(error)
        return("Error: {}".format(error))
    
    finally:
        cursor.close()
        conn.close()
        print('Connection closed.')
        return render_template('home.html', blogs = blogs)
    
@app.route("/blog/")
def blogcontent():
    conn = connect()
    tags = None
    blogid = request.args.get("blogid")
    comments = None
    try:
        cursor = conn.cursor()
        query = "SELECT tag FROM blogstags WHERE blogid = %s"
        args = (blogid,)
        print("Executing query: " + query)
        cursor.execute(query, args)
        tags = cursor.fetchall()
        print("Query result: ", len(tags))

        query = "SELECT commentid,sentiment,description,cdate,username from comments inner join users where authorid = users.userid AND blogid = %s"
        print("Executing query: " + query)
        cursor.execute(query, args)
        comments = cursor.fetchall()
        print("Query result: ", format(comments))

        query = "SELECT blogid,subject,description,pdate,username FROM blogs INNER JOIN users ON users.userid = blogs.userid WHERE blogid = %s"
        print("Executing query: " + query)
        cursor.execute(query,args)
        blog = cursor.fetchone()
        print("Query result: ", format(blog))
        
    except Error as error:
        print(error)
        return("Error: {}".format(error))
    
    finally:
        cursor.close()
        conn.close()
        print('Connection closed.')
        return render_template("blogview.html", blog=blog, comments = comments, tags = tags)

@app.route("/blog/newcomment/", methods = ['POST', 'GET'])
def newcomment():
    conn = connect()
    #RULES:
    #1) USER MUST BE LOGGED IN TO POST A COMMENT
    #2) USER CAN POST AT MOST 1 COMMENT FOR A BLOG
    #3) USER CANNOT COMMENT ON THEIR OWN BLOG
    if request.method == "POST":
        if "username" in session:
            #If logged in
            query = "SELECT userid FROM blogs WHERE blogid = %s"
            args = (request.args.get("blogid"),)
            cursor = conn.cursor()
            cursor.execute(query,args)
            blogauthor = cursor.fetchone()
            #Satisfies Rule #3
            if blogauthor[0] == session['userid']:
                #Check if logged in user is the author of the blog
                flash("Can't commment on your own blog!")
                return redirect("/blog/?blogid="+request.args.get("blogid")) 
            else:
                #Check if user has already commented on the blog
                query = "SELECT commentid FROM comments where authorid = %s AND blogid = %s"
                args = (session['userid'], request.args.get("blogid"))
                cursor.execute(query,args)
                commentlimit = cursor.fetchone()
                if commentlimit is None:
                    #Post the comment
                    query = "INSERT INTO comments(sentiment,description,cdate,blogid,authorid) VALUES (%s,%s,%s,%s,%s)"
                    args = (request.form['sentiment'],request.form['description'], date.today().strftime("%Y-%m-%d"), request.args.get("blogid"), session['userid'])
                    print("Inserting comment: {}".format(args))
                    cursor.execute(query,args)
                    if cursor.lastrowid:
                        print("Successfully inserted comment: ", cursor.lastrowid)
                        conn.commit()
                        return redirect("/blog/?blogid="+request.args.get("blogid"))
                else:
                    #Already commented on this blog
                    flash("You've already commented on this blog")
                    return redirect("/blog/?blogid="+request.args.get("blogid"))

        else:
            return render_template("login.html",authError = "Please log in before you comment")

@app.route("/login", methods=['POST', 'GET'])
def login():
    error = ""

    if request.method == 'POST':
        user = authorize(request.form['username'], request.form['password'])
        if user is not None:
            session['username'] = user[0]
            session['userid'] = user[1]
            return redirect("/user/"+user[0])
        else:
            error = 'Invalid username/password'
    # the code below is executed if the request method
    # was GET or the credentials were invalid
    return render_template('login.html', authError=error)

@app.route("/user/")
@app.route("/user/<username>")
@app.route("/user/newblogpost", methods = ['POST','GET'])
def user(username=None):
    if 'username' in session:
        conn = connect()
        row = None
        blogs = None
        try: 
            cursor = conn.cursor()
            query = "SELECT username, email FROM users WHERE username = %s"
            args = (session['username'],)
            print("Retreiving data for: ", format(args))
            cursor.execute(query, args)
            row = cursor.fetchone()
            print("Authentication Query Result:", format(row))

            query = "SELECT blogid,subject,description,pdate FROM blogs INNER JOIN users ON users.userid = blogs.userid WHERE users.username = %s"
            print("Executing Query: ", query.format(args))
            cursor.execute(query,args)
            blogs = cursor.fetchall()
            print("Query Result: ", format(blogs))

            if(request.method == 'POST'):
                subject = request.form['subject']
                description = request.form['description']
                tags = request.form['tags']
                print(subject)
                print(description)
                print(tags)
                #############################FINISH THIS THING#######################
                

        except Error as error:
            print(error)
            return("Error: {}".format(error))

        finally:
            cursor.close()
            conn.close()
            print('Connection closed.')
            return render_template('user.html', username=session['username'], row=row, blogs=blogs)
    else:
        return render_template("login.html", authError="Please log in")

@app.route("/register", methods=['POST', 'GET'])
def register():
    error = ""
    if request.method == 'POST':
        if request.form['password'] != request.form['password_confirm']:
            return render_template('register.html', show_reg_form = 1, passwordMismatch = "Passwords do not match", email=request.form['email'], username=request.form['username'])
        
        conn = connect()
        try: 
            cursor = conn.cursor()
            query = "INSERT INTO users(username, password, email) VALUES(%s,%s,%s)"
            args = (request.form['username'], request.form['password'], request.form['email'])
            cursor.execute(query, args)
            print("Attempting to add to table: ", format(args))

            if cursor.lastrowid:
                print("Successfully inserted id: ", cursor.lastrowid)
                conn.commit()
                return render_template("register.html", show_reg_form = 0, userid=cursor.lastrowid, email=request.form['email'], username=request.form['username'])

        except IntegrityError as error:
            print(error)
            return render_template("login.html", authError="Username/email already exists. Please login")
        except Error as error:
            print(error)
            return("Error: {}".format(error))

        finally:
            cursor.close()
            conn.close()
            print('Connection closed.')    

    return render_template('register.html', show_reg_form = 1)

@app.route("/logout")
def logout():
    session.pop('username',None)
    return redirect(url_for('index'))


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    app.debug = True
    app.run()