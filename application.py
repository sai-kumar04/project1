import os

from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
# Check for environment variable
#if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
app.secret_key = "you may not guess this"


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
#engine = create_engine('postgresql://postgres:saikumar04@localhost:5432/dvd_vendor')
db = scoped_session(sessionmaker(bind=engine))
print('Opened database successfully')

@app.route("/", methods=["POST","GET"])
def index():
    #return "Project 1: TODO"
    if "username" not in session:
        return redirect("/signin")

    if request.method == "POST":
        title = request.form['title']
        isbn = request.form['isbn']
        author = request.form['author']
        TITLE = "%"+title+"%"
        books = db.execute("SELECT title, isbn FROM books WHERE title ILIKE :TITLE ORDER BY title ASC LIMIT 5;",{'TITLE':TITLE}).fetchall()

        return render_template('index.html', message = 'books searched', books = books, username = session["username"])
    return render_template('index.html',username = session["username"])

@app.route("/register", methods=['POST','GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        retype = request.form['retype']
        if password != retype :
            return render_template('register.html', message="PASSWORDS DO NOT MATCH")
        elif not username:
            return render_template('register.html', message="Please Enter Username")
        elif not password:
            return render_template('register.html', message="Please Enter Password")
        elif not retype:
            return render_template('register.html', message="Please Confirm Your Password")
        hash = generate_password_hash(password)
        #if db.execute("SELECT * FROM register WHERE name=:username;",{"username":username}).fetchall() is None:
        db.execute("INSERT INTO register (name, password) VALUES (:name,:password);",{"name": username,"password": hash})
        db.commit()
        print("user data inserted")
        return redirect("/signin")
        #else:
        #    return render_template('register.html', message="Already Registered, Please Sign In!")

    else:
        return render_template('register.html')

@app.route("/signin", methods=["POST","GET"])
def signin():
    session.clear()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        #id = db.execute("SELECT id FROM user_data WHERE name=:username",{"username":username}).rowcount()
        id = db.execute("SELECT password FROM register WHERE name=:username;",{"username":username}).fetchone()

        if not username:
            return render_template('signin.html', message='Enter Username')
        elif not password:
            return render_template('signin.html', message='Enter Password')
        elif id is None:
            return render_template('signin.html', message='Please Register: Username Does not exist')
        elif not check_password_hash(id.password,password):
            return render_template('signin.html', message='Password is incorrect')
        session["username"] = username

        return redirect("/")
    return render_template('signin.html', message=None)
@app.route("/logout",methods=["POST","GET"])
def logout():

    session.pop("username",None)

    return redirect('/signin')
@app.route("/index/book/<string:isbn>", methods=["GET", "POST"])
def book(isbn):
    if "username" not in session:
        return redirect(url_for("signin"))
    info = db.execute("SELECT * FROM books WHERE isbn = :isbn;",{"isbn":isbn}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key":"Ah5RMnHvTYX0Kt8U3mlB0g", "isbns": isbn})
    response = res.json()
    data = response["books"]
    id = db.execute("SELECT * FROM register WHERE name=:name;",{"name":session["username"]}).fetchone()

    if request.method == "POST":
        review = request.form["review"]
        rating = request.form["rating"]
        if db.execute("SELECT * FROM review_data WHERE user_id = :id AND isbn = :isbn;",{"id":id.id, "isbn": isbn}).fetchone() == None:
            db.execute("INSERT INTO review_data (isbn,user_id,rating,review) VALUES (:isbn,:user_id,:rating,:review)",{"isbn":isbn,"user_id": id.id,"rating":rating,"review":review})
            db.commit()
        reviews = db.execute("SELECT review FROM review_data WHERE isbn = :isbn;",{"isbn":isbn}).fetchall()

        return render_template("book.html", title = info.title, author = info.author,isbn = isbn, year = info.year, avg = data[0]["average_rating"], ratings = data[0]["work_ratings_count"], reviews = reviews)
    else:
        reviews = db.execute("SELECT review FROM review_data WHERE isbn = :isbn;",{"isbn":isbn}).fetchall()

        return render_template("book.html", title = info.title, author = info.author,isbn = isbn, year = info.year, avg = data[0]["average_rating"], ratings = data[0]["work_ratings_count"], reviews = reviews)



@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    info = db.execute("SELECT * FROM books WHERE isbn = :isbn;",{"isbn":isbn}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key":"Ah5RMnHvTYX0Kt8U3mlB0g", "isbns": isbn})
    if res.status_code != 200:
        return jsonify({"error":"Your request was not successful"})

    response = res.json()
    data = response["books"]

    if info == None:
        return jsonify({"error": "invalid ISBN number"}), 404

    res = {"title": info.title, "author": info.author, "year": info.year, "isbn": isbn, "review_count":data[0]["work_ratings_count"], "average_rating": data[0]["average_rating"]}
    return jsonify(res)

if __name__ == '__main__':
    app.run()
