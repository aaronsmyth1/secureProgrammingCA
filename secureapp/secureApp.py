import os
import sqlite3
from flask import Flask, request, render_template, redirect, session
import secrets
from datetime import timedelta
from functools import wraps
import logging
from log_config import setupLogging
from flask_wtf.csrf import CSRFProtect, CSRFError
from security import hash_password, verify_password

#APP CONFIGURATION
app = Flask(__name__)
csrf = CSRFProtect(app)

# Security configurations
app.config.update({
    "SECRET_KEY": secrets.token_urlsafe(32),
    "SESSION_COOKIE_SECURE": True,
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SAMESITE": "Lax",
    "PERMANENT_SESSION_LIFETIME": timedelta(minutes=30)
})

#Logging configuration
setupLogging()

#Security headers
@app.after_request
def add_headers(res):
    res.headers["Referrer-Policy"] = "no-referrer"
    res.headers['X-Content-Type-Options'] = 'nosniff'
    res.headers['X-Frame-Options'] = 'DENY'
    res.headers['Content-Security-Policy'] = "default-src 'self'"
    return res

#Database file paths
users_db = "users.db"
posts_db = "posts.db"

#Database initialization
def init_user_db():
    if not os.path.exists(users_db):
        conn = sqlite3.connect(users_db)
        conn.execute("""
                     CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        is_admin INTEGER DEFAULT 0
                     )
                        """)
        
        admin_username = "admin"
        admin_password = hash_password("AdminPass123!")
        conn.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
                     (admin_username, admin_password, 1))
        conn.commit()
        conn.close()
        logging.info("Created users.db")

  
def init_posts_db():
    if not os.path.exists(posts_db):
        conn = sqlite3.connect(posts_db)
        conn.execute("""
                CREATE TABLE posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) on DELETE CASCADE
                )
            """)
        conn.commit()
        conn.close()
        logging.info("Created posts.db")


init_user_db()
init_posts_db()

#Database connection helpers
def get_user_db():
    conn = sqlite3.connect(users_db)
    conn.row_factory = sqlite3.Row
    return conn

def get_posts_db():
    conn = sqlite3.connect(posts_db)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_id(username):
    conn = get_user_db()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row["id"] if row else None


#Security validation functions
import re
def valid_username(username):
   return re.fullmatch(r'[A-Za-z0-9_]{3,20}', username) is not None
        
def valid_password(password):
    return 8 <= len(password) <= 64

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        
        conn = get_user_db()
        cursor = conn.cursor()
        cursor.execute("SELECT is_admin FROM users WHERE username = ?", (session["user"],))
        row = cursor.fetchone()
        conn.close()

        if row is None or row["is_admin"] == 0:
            return "Access denied", 403
        
        return f(*args, **kwargs)
    return decorated_function


#routes
@app.route("/")
def home():
    if "user" in session:
        conn = get_posts_db()
        posts = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
        conn.close()
        return render_template("home.html", username=session["user"], posts=posts)
    return redirect("/login")

@app.route("/Register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        admin = False
        if session.get("is_admin"):
            admin = request.form.get("admin") == "on"

        if not valid_username(username):
            return "invalid username. Must be 3-20 characters long and contain only letters, numbers, and underscores."
        if not valid_password(password):
            return "invalid password. Must be between 8 and 64 characters long."

        hashed = hash_password(password)
        conn = get_user_db()

        try:
            logging.info(f"Registering user: {username}")
            conn.execute("INSERT INTO users (username, password, is_admin) values (?, ?, ?)",
                           (username, hashed, int(admin)))
            conn.commit()
        except sqlite3.IntegrityError:
            return "username already exists"
        finally:
            conn.close()

        return redirect("/login")
     
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        
        username = request.form["username"]
        password = request.form["password"]
        
        conn = get_user_db()
        row = conn.execute("SELECT * FROM users Where username = ?",(username,)).fetchone()
        conn.close()

        if not row or not verify_password(row["password"], password):
            logging.warning(f"Failed login for: {username}")
            return "invalid username or password"
        
        logging.info(f"User logged in: {username}")
        session["user"] = username
        session["is_admin"] = bool(row["is_admin"])
        return redirect("/")
    
    return render_template("login.html")

#admin page
@app.route("/admin")
@admin_required
def admin_page():
    if not session.get("is_admin"):
        return "Access denied", 403
    conn = get_posts_db()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html", posts=posts, username=session["user"])

#create post
@app.route("/create_post", methods=["GET", "POST"])
@login_required
def create_post(): 
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        username = session["user"]
        user_id = get_user_id(session["user"])

        conn = get_posts_db()
        conn.execute("INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
                     (user_id, title, content))
        conn.commit()
        conn.close()
        logging.info(f"Post created by user: {username}")
        return redirect("/")
    
    return render_template("create_post.html")

#edit post
@app.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    user_id = get_user_id(session["user"])
    conn = get_posts_db()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()

    if not post or (post["user_id"] != user_id and not session.get("is_admin")):
        conn.close()
        return "You cant edit this post", 403
    
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        conn.execute("UPDATE posts SET title = ?, content = ? WHERE id = ?",
                     (title, content, post_id))
        conn.commit()
        conn.close()
        logging.info(f"Post {post_id} edited by user: {session['user']}")
        return redirect("/")
    
    conn.close()
    return render_template("edit_post.html", post=post)

#delete post
@app.route("/delete_post/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    user_id = get_user_id(session["user"])
    conn = get_posts_db()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()

    if not post or (post["user_id"] != user_id and not session.get("is_admin")):
        conn.close()
        return "You cant delete this post", 403
    
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    logging.info(f"Post {post_id} deleted by user: {session['user']}")
    return redirect("/")

@app.route("/search")
def search():
    q = request.args.get("q", "")
    return render_template("search.html", q=q)

@app.route("/admin_logs")
@admin_required
def admin_logs():
    logs_file_path = "app.log"
    logs = []

    try:
        with open(logs_file_path, "r") as f:
            logs = f.readlines()
    except FileNotFoundError:
        logging.error("Log file not found.")

        logs.reverse()
    return render_template("admin_logs.html", logs=logs, usersname=session["user"])

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    logging.warning(f"CSRF error: {e.description}")
    return render_template('csrf_error.html', message=e.description), 400

@app.route("/logout")
def logout():
    username = session.get("user", "unknown")
    session.clear()
    logging.info(f"User logged out: {username}")
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug = True)
