# Git practice
import email

from PIL import Image
from dotenv import load_dotenv
import os
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime 
from datetime import datetime, timedelta  
from functools import wraps
from flask import Flask, render_template, request, session, flash, redirect, url_for
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import uuid
app = Flask(__name__)
load_dotenv()

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME")

serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

mail = Mail(app)


def log_activity(username, action, details=""):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO audit_log (username, action, details)
        VALUES (?, ?, ?)
        """,
        (username, action, details)
    )

    conn.commit()
    conn.close()


UPLOAD_FOLDER = os.path.join("static", "profile_pictures")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

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
def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip().lower()
        password = request.form["password"]

        print("Username entered:", repr(username))
        print("Password entered:", repr(password))

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT username, password, role, active,
                   failed_attempts, locked_until
            FROM users
            WHERE LOWER(username)=?
        """, (username,))

        user = cursor.fetchone()

        # User not found
        if not user:
            flash("Invalid username or password.")
            conn.close()
            return redirect(url_for("login"))

        failed_attempts = user[4] or 0
        locked_until = user[5]

        print("FAILED ATTEMPTS =", failed_attempts)
        print("LOCKED UNTIL =", locked_until)

        # Account locked?
        if locked_until:
            unlock_time = datetime.fromisoformat(locked_until)

            if datetime.now() < unlock_time:
                flash(
                    f"Your account is locked until {unlock_time.strftime('%H:%M:%S')}."
                )
                conn.close()
                return redirect(url_for("login"))

        # Correct password
        if check_password_hash(user[1], password):

            # Account inactive
            if user[3] == 0:
                flash("Your account has been deactivated. Please contact the administrator.")
                conn.close()
                return redirect(url_for("login"))

            # Reset lock information
            cursor.execute("""
                UPDATE users
                SET failed_attempts=0,
                    locked_until=NULL
                WHERE LOWER(username)=?
            """, (username,))

            conn.commit()

            session["username"] = user[0]
            session["role"] = user[2]

            log_activity(
                session["username"],
                "Login",
                "Successful login"
            )

            conn.close()

            return redirect(url_for("dashboard"))

        # Wrong password
        failed_attempts += 1

        if failed_attempts >= 5:

            locked_until = (
                datetime.now() + timedelta(minutes=15)
            ).isoformat()

            cursor.execute("""
                UPDATE users
                SET failed_attempts=0,
                    locked_until=?
                WHERE LOWER(username)=?
            """, (locked_until, username))

            flash(
                "Too many failed login attempts. "
                "Your account has been locked for 15 minutes."
            )

        else:

            cursor.execute("""
                UPDATE users
                SET failed_attempts=?
                WHERE LOWER(username)=?
            """, (failed_attempts, username))

            flash(
                f"Invalid username or password. "
                f"Attempt {failed_attempts} of 5."
            )

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Total admins
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    total_admins = cursor.fetchone()[0]

    # Total regular users
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='user'")
    total_regular_users = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_users=total_users,
        total_admins=total_admins,
        total_regular_users=total_regular_users
    )

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"].strip()

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()
        conn.close()

        if not user:
            flash("No account is registered with that email.")
            return redirect(url_for("forgot_password"))

        # Generate a secure token
        token = serializer.dumps(email, salt="password-reset")

        # Create the reset link
        reset_link = url_for(
            "reset_password_token",
            token=token,
            _external=True
        )

        # Create the email
        msg = Message(
            "Password Reset Request",
            recipients=[email]
        )

        msg.body = f"""
Hello,

We received a request to reset your password.

Click the link below to choose a new password:

{reset_link}

If you did not request a password reset, simply ignore this email.

This link will expire for security reasons.

Joshua Flask App
"""

        mail.send(msg)
        flash("A password reset link has been sent to your email.")
        return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/admin_dashboard")
@login_required
def admin_dashboard():

    if session.get("role") != "admin":
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT username, email, role, created_at
    FROM users
    WHERE username=?
    """, (session["username"],))

    admin = cursor.fetchone()

    member_since = ""

    if admin[3]:
        member_since = datetime.strptime(
            admin[3], "%Y-%m-%d"
        ).strftime("%d %B %Y")
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    # Total admins
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    total_admins = cursor.fetchone()[0]

    # Total regular users
    cursor.execute("SELECT COUNT(*) FROM users WHERE role='user'")
    total_regular_users = cursor.fetchone()[0]

    # Users with email
    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE email IS NOT NULL
        AND email != ''
    """)
    users_with_email = cursor.fetchone()[0]

    # Users without email
    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE email IS NULL
        OR email = ''
    """)
    users_without_email = cursor.fetchone()[0]

    # Recent users
    cursor.execute("""
    SELECT username, email, role
    FROM users
    ORDER BY rowid DESC
    LIMIT 5
""")
    recent_users = cursor.fetchall()

    conn.close()

    return render_template(
    "admin_dashboard.html",
    total_users=total_users,
    total_admins=total_admins,
    total_regular_users=total_regular_users,
    users_with_email=users_with_email,
    users_without_email=users_without_email,
    recent_users=recent_users,
    admin=admin,
    member_since=member_since
)



# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    log_activity(
    session["username"],
    "Logout",
    "User logged out"
   )
    session.pop("username", None)
    flash("You have logged out")
    return redirect(url_for("home"))

# ---------------- REGISTER ----------------
@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"].strip()
    email = request.form["email"].strip()
    password = request.form["password"].strip()

    if username == "" or password == "":
        return render_template("register_result.html",
                               message="Username and password are required")

    db = sqlite3.connect("users.db")
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        flash("Username already exists")
        return redirect(url_for("register_page"))
    password = request.form["password"]
    hashed_password = generate_password_hash(password)

    created_at = datetime.now().strftime("%Y-%m-%d")

    if session.get("role") == "admin":
        role = request.form.get("role", "user")
    else:
        role = "user"

    cursor.execute(
        """
        INSERT INTO users (username, password, role, email, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (username, hashed_password, role, email, created_at)
    )

    db.commit()
    db.close()

    flash("User registered successfully")
    return redirect(url_for("login"))

@app.route("/add_user")
@login_required
def add_user():
    if session.get("role") != "admin":
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    return redirect(url_for("register_page"))
# ---------------- PROFILE ----------------
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if request.method == "POST":

        # Update email
        email = request.form["email"].strip()

        cursor.execute(
            """
            UPDATE users
            SET email=?
            WHERE username=?
            """,
            (email, session["username"])
        )

        # Upload profile picture
        if "profile_picture" in request.files:

            file = request.files["profile_picture"]

            if file.filename != "" and allowed_file(file.filename):

                extension = file.filename.rsplit(".", 1)[1].lower()
                filename = f"{uuid.uuid4()}.{extension}"

                filepath = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )

                cursor.execute(
                """
                SELECT profile_picture
                FROM users
               WHERE username=?
               """,
               (session["username"],)
      )

                old_picture = cursor.fetchone()[0]
                print("OLD PICTURE =", old_picture)
                file.save(filepath)

                # Open image
                image = Image.open(filepath)

                # Crop to square
                width, height = image.size

                if width > height:
                    left = (width - height) // 2
                    top = 0
                    right = left + height
                    bottom = height
                else:
                    left = 0
                    top = (height - width) // 2
                    right = width
                    bottom = top + width

                image = image.crop((left, top, right, bottom))

                # Resize
                image = image.resize((200, 200), Image.LANCZOS)

                image.save(filepath)

                # Delete the previous picture (but keep the default image)
                if old_picture and old_picture != "default.jpg":

                 old_path = os.path.join(
                 app.config["UPLOAD_FOLDER"],
                 old_picture
         )
                 print("Old path:", old_path)
                 print("Exists?", os.path.exists(old_path))
                 if os.path.exists(old_path):
                  os.remove(old_path)


                # Save filename to database
                cursor.execute(
                    """
                    UPDATE users
                    SET profile_picture=?
                    WHERE username=?
                    """,
                    (filename, session["username"])
           )  

        conn.commit()
        flash("Profile updated succes sfully!")

    cursor.execute(
        """
        SELECT username,
               email,
               role,
               created_at,
               profile_picture
        FROM users
        WHERE username=?
        """,
        (session["username"],)
    )

    user = cursor.fetchone()
    print("SESSION USERNAME =", session["username"])
    print("USER =", user)
    conn.close()

    from datetime import datetime

    member_since = ""

    if user[3]:
        member_since = datetime.strptime(
            user[3],
            "%Y-%m-%d"
        ).strftime("%d %B %Y")

    return render_template(
        "profile.html",
        username=user[0],
        email=user[1],
        role=user[2],
        created_at=member_since,
        profile_picture=user[4] if len(user) > 4 else None
    )

@app.route("/users")
@login_required
def users():

    if session.get("role") != "admin":
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()

    per_page = 5
    offset = (page - 1) * per_page

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if search:
        like = "%" + search + "%"

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE username LIKE ?
            """,
            (like,)
        )

        total_users = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT username, email, role
            FROM users
            WHERE username LIKE ?
            ORDER BY username
            LIMIT ? OFFSET ?
            """,
            (like, per_page, offset)
        )

    else:

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT username, email, role, active
            FROM users
            ORDER BY username
            LIMIT ? OFFSET ?
            """,
            (per_page, offset)
        )

    users = cursor.fetchall()
    conn.close()

    total_pages = (total_users + per_page - 1) // per_page

    return render_template(
        "users.html",
        users=users,
        page=page,
        total_pages=total_pages,
        search=search
    )

@app.route("/toggle_user/<username>")
@login_required
def toggle_user(username):

    print("TOGGLE USER ROUTE CALLED:", username)

    # Only admins can change account status
    if session.get("role") != "admin":
        flash("Access denied.")
        return redirect(url_for("users"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Get current status
    cursor.execute(
        "SELECT active FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    if user is None:
        flash("User not found.")
        conn.close()
        return redirect(url_for("users"))

    # Prevent an admin from deactivating themselves
    if username.lower() == session["username"].lower():
       flash("You cannot deactivate your own account.")
       conn.close()
       return redirect(url_for("users"))

    # Toggle status
    new_status = 0 if user[0] == 1 else 1

    cursor.execute( 
        """
        UPDATE users
        SET active=?
        WHERE username=?
        """,
        (new_status, username)
    )

    status = "Activated" if new_status == 1 else "Deactivated"

    conn.commit()
    conn.close()

    log_activity(
        session["username"],
        status,
        f"{status} user '{username}'"
    )

    flash("User status updated successfully.")

    return redirect(url_for("users"))



@app.route("/edit_user/<username>", methods=["GET", "POST"])
@login_required
def edit_user(username):

    if session.get("role") != "admin":
        flash("Access denied.")
        return redirect(url_for("users"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    if request.method == "POST":

        new_username = request.form["username"].strip()
        new_email = request.form["email"].strip()
        new_role = request.form["role"]
        new_active = int(request.form["active"])
        print("NEW ACTIVE =", new_active)
        
        cursor.execute(
            """
            SELECT username
            FROM users
            WHERE username=? AND username<>?
            """,
            (new_username, username)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            flash("Username already exists!", "danger")
            conn.close()
            return redirect(url_for("edit_user", username=username))

        if username == session.get("username") and new_role != "admin":
            flash("You cannot remove your own administrator role.")
            conn.close()
            return redirect(url_for("users"))

        if username == session.get("username") and new_active == 0:
            flash("You cannot deactivate your own account.")
            conn.close()
            return redirect(url_for("users"))

        cursor.execute(
            """
            UPDATE users
            SET username=?, email=?, role=?, active=?
            WHERE username=?
            """,
            (new_username, new_email, new_role, new_active, username)
        )

        conn.commit()
        log_activity(
            session["username"],
            "Edit User",
            f"Updated user '{new_username}'"
        )
        conn.close()

        flash("User updated successfully.")
        return redirect(url_for("users"))

    cursor.execute(
        "SELECT username, email, role, active FROM users WHERE username=?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()

    return render_template(
        "edit_user.html",
        user=user
    )

@app.route("/reset_password/<username>", methods=["GET", "POST"])
@login_required
def reset_password(username):

    if session.get("role") != "admin":
        flash("Access denied.")
        return redirect(url_for("users"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    if user is None:
        conn.close()
        flash("User account not found.")
        return redirect(url_for("forgot_password"))

    
    if request.method == "POST":

        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not new_password or not confirm_password:
            flash("All fields are required.")
            conn.close()
            return redirect(url_for("reset_password", username=username))

        if new_password != confirm_password:
            flash("Passwords do not match.")
            conn.close()
            return redirect(url_for("reset_password", username=username))

        hashed = generate_password_hash(new_password)

        cursor.execute(
            "UPDATE users SET password=? WHERE username=?",
            (hashed, username)
        )

        log_activity(
            session["username"],
            "Reset Password",
            f"Reset password for '{username}'"
        )

        conn.commit()
        conn.close()

        flash(f"Password for {username} has been reset successfully.")
        return redirect(url_for("users"))

    conn.close()
    return render_template(
        "reset_password.html",
        username=username
    )
@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_password_token(token):

    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=3600
        )

    except Exception:
        flash("This password reset link is invalid or has expired.")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not new_password or not confirm_password:
            flash("All fields are required.")
            return redirect(url_for("reset_password_token", token=token))

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("reset_password_token", token=token))

        hashed = generate_password_hash(new_password)

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT username FROM users WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()

        if user is None:
            conn.close()
            flash("User account not found.")
            return redirect(url_for("forgot_password"))

        cursor.execute(
            "UPDATE users SET password=? WHERE email=?",
            (hashed, email)
        )

        conn.commit()
        conn.close()

        log_activity(
            user[0],
            "Password Reset",
            "Password reset using email link"
        )

        flash("Your password has been reset successfully. Please log in.")
        return redirect(url_for("login"))

    return render_template("reset_password_token.html")

@app.route("/delete_user/<username>")
@login_required
def delete_user(username):

    # Only admins can delete users
    if session.get("role") != "admin":
        flash("Access denied.")
        return redirect(url_for("users"))
    
    log_activity(
    session["username"],
    "Delete User",
    f"Deleted user '{username}'"
)

    # Prevent an admin from deleting their own account
    if username == session.get("username"):
        flash("You cannot delete your own account.")
        return redirect(url_for("users"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE username=?",
        (username,)
    )

    conn.commit()
    conn.close()

    flash(f"User '{username}' deleted successfully.")

    return redirect(url_for("users"))

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
        log_activity(
           session["username"],
           "Change Password",
           "Changed own password"
)
        db.commit()
        db.close()

        flash("Password changed successfully.", "success")

        return redirect(url_for("dashboard"))

    return render_template("change_password.html")

@app.route("/audit_log")
@login_required
def audit_log():

    if session.get("role") != "admin":
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT username, action, details, created_at
        FROM audit_log
        ORDER BY id DESC
    """)

    logs = cursor.fetchall()
    conn.close()

    return render_template("audit_log.html", logs=logs)
@app.route("/test_email")
@login_required
def test_email():

    try:
        msg = Message(
            subject="Flask Email Test",
            recipients=["machogujosh@gmail.com"]
        )

        msg.body = """
Congratulations!

Your Flask application has successfully sent this email using Gmail.

- Joshua's Flask Project
"""

        mail.send(msg)

        return "Email sent successfully!"

    except Exception as e:
        return f"Error: {e}"

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)