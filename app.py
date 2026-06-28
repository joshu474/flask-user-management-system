from functools import wraps
from flask import Flask, render_template, request, session, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "123"  # Add a secret key for session management

@app.route("/")
def home():
    return redirect(url_for("login"))

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"]

        print("USERNAME ENTERED =", repr(username))
        print("PASSWORD ENTERED =", repr(password))

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE LOWER(username)=?",
            (username, )
        )

        username = cursor.fetchone()
        print("USERNAME =", username)
        conn.close( )

        if username and check_password_hash(username[1], password):
            session["username"] = username[0]
            return redirect(url_for("dashboard"))

        print("LOGIN FAILED")
        flash("Invalid username or password")

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    TOTAL_USERS = cursor.fetchone()[0] 

    conn.close()

    return render_template(
        "dashboard.html",
        total_users=TOTAL_USERS
    )


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You have logged out")
    return redirect(url_for("home"))

# ---------------- REGISTER ----------------
@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    if username == "" or password == "":
        return render_template("register_result.html",
                               message="Username and password are required")

    db = sqlite3.connect("users.db")
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        flash("Username already exists")
        return redirect(url_for("register"))
    password = request.form["password"]
    hashed_password = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users(username, password) VALUES (?, ?)",
                       (username, hashed_password))
    db.commit()
    db.close()
    flash("User registered successfuilly")
    return redirect(url_for("login"))

# ---------------- PROFILE ----------------
@app.route("/profile")
@login_required
def profile():   # ✅ function name matches url_for('profile')
    if "username" not in session:
        flash("Please log in first")
    return redirect(url_for("home"))

    return render_template("profile.html", username=session["username"])

# ---------------- EDIT PROFILE ----------------
@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        new_username = request.form["username"].strip()

        if not new_username:
            flash("Username is required.")
            return redirect(url_for("edit_profile"))

        new_username = new_username.lower()
        current_username = session["username"].lower()

        db = sqlite3.connect("users.db")
        cursor = db.cursor()

        cursor.execute(
            "SELECT username FROM users WHERE LOWER(username)=? AND LOWER(username)!=?",
            (new_username, current_username)
        )
        if cursor.fetchone():
            db.close()
            flash("Username already exists.")
            return redirect(url_for("edit_profile"))

        cursor.execute(
            "UPDATE users SET username=? WHERE LOWER(username)=?",
            (new_username, current_username)
        )
        db.commit()
        db.close()

        session["username"] = new_username
        flash("Profile updated successfully!")
        return redirect(url_for("dashboard"))

    return render_template("edit_profile.html")

@app.route("/users")
@login_required
def users():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template(
        "users.html",
        users=users
    )

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not current_password or not new_password or not confirm_password:
            flash("All password fields are required.")
            return redirect(url_for("change_password"))

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("change_password"))

        db = sqlite3.connect("users.db")
        cursor = db.cursor()

        cursor.execute(
            "SELECT password FROM users WHERE LOWER(username)=?",
            (session["username"].lower(),)
        )
        user = cursor.fetchone()

        if not user:
            db.close()
            flash("User not found.")
            return redirect(url_for("change_password"))

        stored_hash = user[0]
        if not check_password_hash(stored_hash, current_password):
            db.close()
            flash("Current password is incorrect")
            return redirect(url_for("change_password"))

        hashed = generate_password_hash(new_password)
        cursor.execute(
            "UPDATE users SET password=? WHERE LOWER(username)=?",
            (hashed, session["username"].lower())
        )
        db.commit()
        db.close()
        flash("Password changed successfully!")
        return redirect(url_for("dashboard"))

    return render_template("change_password.html")
# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)
