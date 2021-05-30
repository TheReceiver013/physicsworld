from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import random
import datetime

from helpers import apology, login_required

app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///all.db")
schools = {"RHOSS":"14/2/2005"}
students = [["user1", "offline"], ["user2", "offline"], ["user3", "offline"], ["user4", "offline"], ["user5", "offline"]]


@app.route("/sregister", methods=["GET", "POST"])
def sregister():
    if request.method == "POST":
        username = request.form.get("names")
        password = request.form.get("pass")
        confirmation = request.form.get("confirm")
        inputID = request.form.get("schoolID")
        classs = request.form.get("class")
        level = request.form.get("level")
        hashp = generate_password_hash(password)
        teacherID = request.form.get("teacherID")
        question = request.form.get("question")
        answer = request.form.get("answer")
        email = request.form.get("email")

        if not username:
            return apology("Must provide username!")
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) > 0:
            return apology("This username is unavailable.")
        elif not email:
            return apology("Must write your email.")
        elif not password:
            return apology("Must provide password!")
        elif not confirmation:
            return apology("Must confirm password!")
        elif not inputID:
            return apology("Must provide school's code!")
        elif not level:
            return apology("Must provide if you are a student or teacher.")
        elif confirmation != password:
            return apology("Passwords should be the same!")
        elif inputID != "14/2/2005":
            return apology("Invalid school code.")
        elif level == "Student":
            if not classs:
                return apology("Class name is missing!")
        elif level == "Teacher":
            if not teacherID:
                return apology("Must provide teacher's code.")
        elif not question or not answer:
            return apology("Must complete security question part.")
        schoolID = inputID

        db.execute("INSERT INTO users (username, pass, schoolID, level, class, score, email) VALUES(?, ?, ?, ?, ?, ?, ?)", username, password, schoolID, level, classs, 0, email)
        db.execute("INSERT INTO securityQ VALUES(?,?,?)", username, question, answer)
        return redirect("/login")
    else:
        names = []
        for student in students:
            names.append(student[0])
        return render_template("sregister.html", schools=schools, names=names)

@app.route("/gregister", methods=["GET", "POST"])
def gregister():
    rows = db.execute("SELECT * FROM users")
    if request.method == "POST":
        if request.form.get("login") == "login":
            return redirect("/")
        username = request.form.get("username")
        password = request.form.get("pass")
        confirmation = request.form.get("confirm")
        email = request.form.get("email")
        question = request.form.get("question")
        answer = request.form.get("answer")
        classs = request.form.get("class")

        if not username:
            return apology("Must provide username!")
        elif not email:
            return apology("Must provide email")
        elif not password:
            return apology("Must provide password!")
        elif not confirmation:
            return apology("Must confirm password!")
        elif confirmation != password:
            return apology("Passwords should be the same!")
        elif not question or not answer:
            return apology("Must complete security question part.")

        db.execute("INSERT INTO users (username, pass, class, score, email, level) VALUES(?, ?, ?, ?, ?,?)", username, password, classs, 0, email, "no")
        db.execute("INSERT INTO securityQ VALUES(?,?,?)", username, question, answer)
        return redirect("/login")
    else:
        return render_template("gregister.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("pass")
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) == 1:
            user_id = rows[0]['id']

        if not username:
            return apology("Must provide username!")
        elif not password:
            return apology("Must provide password!")
        elif len(rows) != 1 or password != rows[0]['pass']:
            return apology("INVALID username or password")
        if len(rows) == 1:
            session['user_id'] = user_id

        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/forgetPassword", methods=['POST', 'GET'])
def checkQ():
    if request.method == "POST":
        question = request.form.get("question")
        answer = request.form.get("answer")
        username = request.form.get("username")
        check = db.execute("SELECT * FROM securityQ WHERE username = ?", username)
        check = check[0]
        if question != check['question'] or answer != check['answer']:
            return apology("INVALID INPUT.")
        return render_template("changePassword.html", username=username)

    else:
        return render_template("checkQ.html")

@app.route("/changePass", methods=['POST'])
def changePass():
    username = request.form.get("username")
    newpass = request.form.get("newpass")
    db.execute("UPDATE users SET pass = ? WHERE username = ?", newpass, username)
    return redirect("/login")


@app.route("/")
@login_required
def index():
    user_id = session['user_id']
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    classs = user[0]['class']
    quotes = db.execute("SELECT * FROM quotes")
    id_list = []
    for quote in quotes:
        id_list.append(quote['id'])
    goal = random.choice(id_list)
    quotes = db.execute("SELECT * FROM quotes WHERE id = ?", goal)
    quote = quotes[0]['quote']
    writer = quotes[0]['writer']
    likes = quotes[0]['likes']
    loves = quotes[0]['loves']

    today = datetime.datetime.today().strftime('%Y%m%d')
    posts = db.execute("SELECT * FROM daily WHERE date = ?", today)

    return render_template("index.html", quote=quote, writer=writer, likes=likes, loves=loves, posts=posts, classs=classs)

@app.route("/choose")
@login_required
def choose():
    return redirect(url_for("chooseLevel", level="level"))

@app.route("/choose/<level>", methods=['POST', 'GET'])
@login_required
def chooseLevel(level):
    if request.method == "POST":
        level = request.form.get("level")
        return redirect(url_for("chooseUnit", level=level, unit="unit"))
    else:
        levels = db.execute("SELECT DISTINCT(level) FROM pset")
        return render_template("chooseLevel.html", levels=levels)


@app.route("/choose/<level>/<unit>", methods=['POST', 'GET'])
@login_required
def chooseUnit(level, unit):
    if request.method == "POST":
        unit = request.form.get("unit")
        if unit == "random":
            if level == "random":
                problems = db.execute("SELECT * FROM pset")
            else:
                problems = db.execute("SELECT * FROM pset WHERE level = ?", level)
            id_list = []
            for problem in problems:
                id_list.append(problem['id'])
            problem_id = random.choice(id_list)
            problem = db.execute("SELECT * FROM pset WHERE id = ?", problem_id)
            topic = problem[0]['topic']
            return render_template("findProblem.html", topic=topic, problem_id=problem_id)
        return redirect(url_for("chooseLesson", level=level, unit=unit, lesson="lesson"))
    else:
        if level == "random":
            unitss = db.execute("SELECT DISTINCT(unit) FROM pset")
        else:
            unitss = db.execute("SELECT DISTINCT(unit) FROM pset WHERE level = ?", level)
        units = []
        for unit in unitss:
            units.append(unit['unit'])
        return render_template("chooseUnit.html", units=units, level=level)

@app.route("/choose/<level>/<unit>/<lesson>", methods=['POST', 'GET'])
@login_required
def chooseLesson(level, unit, lesson):
    if request.method == "POST":
        lesson = request.form.get("lesson")
        if lesson == "random":
            if level == "random":
                problems = db.execute("SELECT * FROM pset WHERE unit = ?", unit)
            else:
                problems = db.execute("SELECT * FROM pset WHERE level = ? AND unit = ?", level, unit)
            id_list = []
            for problem in problems:
                id_list.append(problem['id'])
            problem_id = random.choice(id_list)
            problem = db.execute("SELECT * FROM pset WHERE id = ?", problem_id)
            topic = problem[0]['topic']
            return render_template("findProblem.html", topic=topic, problem_id=problem_id)
        return redirect(url_for("chooseTopic", level=level, unit=unit, lesson=lesson, topic="topic"))
    else:
        if level == "random":
            lessonss = db.execute("SELECT DISTINCT(lesson) FROM pset WHERE unit = ?", unit)
        else:
            lessonss = db.execute("SELECT DISTINCT(lesson) FROM pset WHERE level = ? AND unit = ?", level, unit)
        lessons = []
        for lesson in lessonss:
            lessons.append(lesson['lesson'])
        return render_template("chooseLesson.html", lessons=lessons, unit=unit, level=level)

@app.route("/choose/<level>/<unit>/<lesson>/<topic>", methods=['POST', 'GET'])
@login_required
def chooseTopic(level, unit, lesson, topic):
    if request.method == "POST":
        topic = request.form.get("topic")
        if topic == "random":
            if level == "random":
                problems = db.execute("SELECT * FROM pset WHERE lesson = ?", lesson)
            else:
                problems = db.execute("SELECT * FROM pset WHERE level = ? AND lesson = ?", level, lesson)
            id_list = []
            for problem in problems:
                id_list.append(problem['id'])
            problem_id = random.choice(id_list)
            problem = db.execute("SELECT * FROM pset WHERE id = ?", problem_id)
            topic = problem[0]['topic']
            return render_template("findProblem.html", topic=topic, problem_id=problem_id)
        else:
            if level == "random":
                problems = db.execute("SELECT * FROM pset WHERE topic = ?", topic)
            else:
                problems = db.execute("SELECT * FROM pset WHERE level = ? AND topic = ?", level, topic)
            id_list = []
            for problem in problems:
                id_list.append(problem['id'])
            problem_id = random.choice(id_list)
            problem = db.execute("SELECT * FROM pset WHERE id = ?", problem_id)
            topic = problem[0]['topic']
            return render_template("findProblem.html", topic=topic, problem_id=problem_id)
    else:
        if level == "random":
            topicss = db.execute("SELECT DISTINCT(topic) FROM pset WHERE lesson = ?", lesson)
        else:
            topicss = db.execute("SELECT DISTINCT(topic) FROM pset WHERE level = ? AND lesson = ?", level, lesson)
        topics = []
        for topic in topicss:
            topics.append(topic['topic'])
        return render_template("chooseTopic.html", topics=topics, level=level, lesson=lesson, unit=unit)


@app.route("/learn", methods=['POST', 'GET'])
@login_required
def learn():
    if request.method == "POST":
        if request.form.get("find") == "true":
            topic = request.form.get("topic")
            problem_id = int(request.form.get("problem_id"))
            return redirect(url_for("problem", topic=topic, problem="problem", problem_id=problem_id))
        else:
            topic = request.form.get("topic")
            problem_id = request.form.get("problem_id")
            if problem_id == "nth":
                return redirect(url_for("info", topic=topic, info="info"))
            else:
                return redirect(url_for("problem", topic=topic, problem="problem", problem_id=problem_id))
    else:
        units = db.execute("SELECT DISTINCT(unit) FROM pset")
        lessons = db.execute("SELECT DISTINCT(lesson), unit FROM pset")
        topics = db.execute("SELECT DISTINCT(topic), lesson, id FROM pset")
        problems = db.execute("SELECT * FROM pset")
        return render_template("stuff.html", units=units, lessons=lessons, topics=topics, problems=problems, find="false")

@app.route("/learn/<topic>/<info>")
@login_required
def info(topic, info):
    row = db.execute("SELECT * FROM info WHERE topic = ?", topic)
    info_id = row[0]['id']
    parts = db.execute("SELECT * FROM parts WHERE info_id = ?", info_id)
    return render_template("info.html", parts=parts, info_id=info_id)

@app.route("/learn/<topic>/<problem>/<problem_id>", methods=['POST', 'GET'])
@login_required
def problem(topic, problem, problem_id):
    user_id = session['user_id']
    today = datetime.datetime.today().strftime('%Y%m%d')
    problem_id = int(problem_id)
    row = db.execute("SELECT * FROM pset WHERE id = ?", problem_id)
    problem = row[0]
    radios = db.execute("SELECT * FROM radios WHERE problem_id = ?", problem_id)
    solutions = db.execute("SELECT * FROM solutions WHERE problem_id = ?", problem_id)
    solved = db.execute("SELECT * FROM track WHERE user_id = ? AND problem_id = ?", user_id, problem_id)
    if len(solved) == 0:
        loss = "true"
    else:
        loss = "false"
    if request.method == 'POST':
        if len(solved) == 0:
            loose = request.form.get("go")
            if loose == "true":
                if problem['level'] == "easy":
                    lost = 2
                elif problem['level'] == "medium":
                    lost = 4
                else:
                    lost = 6
                db.execute("INSERT INTO openSol VALUES(?,?)", user_id, problem_id)
                db.execute("INSERT INTO track VALUES(?,?,?)", user_id, problem_id, today)
                db.execute("UPDATE users SET score = score - ? WHERE id = ?", lost, user_id)

                return render_template("solution.html", sol=problem['solution'], minisols=solutions)
            detectError = 0
            if problem['type'] == "choose":
                answ = request.form.get("radio")
                sol = solutions[0]
                if answ != sol['solution']:
                    detectError += 1
            else:
                for sol in solutions:
                    answ = request.form.get(f"{sol['id']}")
                    if answ != sol['solution']:
                        detectError += 1
            if request.form.get("submit") == "submit":
                if detectError > 0:
                    rxn = "Incorrect!"
                else:
                    rxn = "Correct!"
                    if problem['level'] == "easy":
                        add = 2
                    elif problem['level'] == "medium":
                        add = 4
                    else:
                        add = 7

                    db.execute("INSERT INTO track VALUES(?,?,?)", user_id, problem_id, today)
                    db.execute("UPDATE users SET score = score + ? WHERE id = ?", add, user_id)
            else:
                rxn = ""
        else:
            rxn = "It seems you have solved this problem already!!"
        return render_template("problem.html", problem=problem, radios=radios, solutions=solutions, rxn=rxn, loss=loss, submited="true", problem_name=problem['problem_name'])
    else:
        return render_template("problem.html", topic=topic, problem=problem, radios=radios, solutions=solutions, rxn="", loss=loss, submited="false", problem_name=problem['problem_name'])

@app.route("/add", methods=['POST', 'GET'])
@login_required
def problemTy():
    if request.method == "POST":
        typee = request.form.get("type")
        return redirect(url_for("count", typee=typee))
    else:
        return render_template("problemType.html")

@app.route("/add/<typee>", methods=['POST', 'GET'])
@login_required
def count(typee):
    if request.method == "POST":
        nb = int(request.form.get("nb"))
        return redirect(url_for("add", typee=typee, nb=nb))
    else:
        return render_template("nb.html", typee=typee)

@app.route("/add/<typee>/<nb>", methods=['POST', 'GET'])
@login_required
def add(typee, nb):
    user_id = session['user_id']
    if request.method == "POST":
        problem = request.form.get("problem")
        level = request.form.get("level")
        classs = int(request.form.get("class"))
        unit = request.form.get("unit")
        lesson = request.form.get("lesson")
        topic = request.form.get("topic")
        solution = request.form.get("solution")
        problem_name = request.form.get("problem_name")
        sols = []
        radios = []
        nb = int(nb)
        for i in range(nb):
            if typee == "Q-A":
                solKey = "minisol" + str(i)
                sols.append(request.form.get(solKey))
            else:
                radioKey = "radio" + str(i)
                radios.append(request.form.get(radioKey))
        if typee == "Radio":
            typee = "choose"
        if request.form.get("img"):
            img = request.form.get("img")
        else:
            img = ""
        db.execute("INSERT INTO pset (problem, type, level, class, unit, lesson, topic, solution, problem_name, user_id, img) VALUES(?,?,?,?,?,?,?,?,?,?,?)", problem, typee, level, classs, unit, lesson, topic, solution, problem_name, user_id, img)
        rows = db.execute("SELECT * FROM pset WHERE problem = ?", problem)
        if typee == "choose":
            sols.append(request.form.get("minisol"))
            for i in range(nb):
                typee = "choose"
                db.execute("INSERT INTO radios (problem_id, radio) VALUES(?,?)", rows[0]['id'], radios[i])

        for i in range(len(sols)):
            db.execute("INSERT INTO solutions (problem_id, solution) VALUES(?,?)", rows[0]['id'], sols[i])

        return redirect("/")
    else:
        user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
        user = user[0]
        if user['level'] == "no":
            return apology("Oops You must be in the first 3 ranks to use this special feature, work on this.. there is nothing impossible!")
        elif user['level'] == "Student" and user['username'] != "Creator":
            return apology("Oops, this special feature is just for teachers OR who is in the first 3 ranks.. work on that if you want to post daily to your friends/school!")
        units = db.execute("SELECT DISTINCT(unit) FROM pset")
        lessons = db.execute("SELECT DISTINCT(lesson) FROM pset")
        topics = db.execute("SELECT DISTINCT(topic) FROM pset")
        nb = int(nb)
        return render_template("add.html", typee=typee, classes=[11, 12], units=units, lessons=lessons, topics=topics, levels=["easy", "medium", "hard"], nb=nb)

@app.route("/scoreTable", methods=['POST', 'GET'])
@login_required
def scores():
    user_id = session['user_id']
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    classs = user[0]['class']
    students = db.execute("SELECT * FROM users WHERE level = 'Student' OR username = 'Creator' OR level = 'no'")
    teachers = db.execute("SELECT * FROM users WHERE level = 'Teacher'")
    if request.method == "POST":
        mode = request.form.get("mode")
        if not mode:
            return apology("Must choose a mode!")
        elif mode == "School":
            students = db.execute("SELECT * FROM users WHERE level = 'Student' OR username = 'Creator'")
        return render_template("scoreTable.html", students=students, teachers=teachers, mode=mode, classs=classs)


    else:
        mode = "School"
        if user[0]['level'] == "no":
            mode = "Global"
        if mode == "School":
            students = db.execute("SELECT * FROM users WHERE level = 'Student' OR username = 'Creator'")
        return render_template("scoreTable.html", students=students, teachers=teachers, mode=mode, classs=classs)

@app.route("/addDaily", methods=['POST', 'GET'])
@login_required
def addDaily():
    user_id = session['user_id']
    rows = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    username = rows[0]['username']
    if rows[0]['level'] == "no":
        mode = "global"
    else:
        mode = "school"

    if request.method == "POST":
        typee = request.form.get("type")
        title = request.form.get("title")
        text = request.form.get("text")
        today = datetime.datetime.today().strftime('%Y%m%d')
        img = request.form.get("img")
        classs = request.form.get("class")
        db.execute("INSERT INTO daily (user_id, title, text, type, date, img, writer, mode, class) VALUES(?,?,?,?,?,?,?,?,?)", user_id, title, text, typee, today, img, username, mode, classs)

        return redirect("/")
    else:
        user = rows[0]
        if user['level'] == "no":
            return apology("Oops You must be in the first 3 ranks to use this special feature, work on this.. there is nothing impossible!")
        elif user['level'] == "Student" and user['username'] != "Creator":
            return apology("Oops, this special feature is just for teachers OR who is in the first 3 ranks.. work on that if you want to post daily to your friends/school!")
        return render_template("addDaily.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)