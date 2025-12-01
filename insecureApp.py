import os
import sqlite3
from flask import Flask, request, render_template, redirect, session

app = Flask(__name__)
app.secret_key = "123"

users_db = "users.db"
posts_db = "posts.db"

def init_user_db():
    if not os.path.exists(users_db):
        conn = sqlite3.connect(users_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

def init_posts_db():
    if not os.path.exists(posts_db):
        conn = sqlite3.connect(posts_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

init_user_db()
init_posts_db()

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

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")

    conn = get_posts_db()
    posts = conn.execute("SELECT * FROM posts").fetchall()
    conn.close()

    return render_template("home.html", username=session["user"], posts=posts)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_user_db()

        query = f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')"

        try:
            conn.execute(query)
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists"
        
        conn.close()
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_user_db()

        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"

        user = conn.execute(query).fetchone()
        conn.close()

        if user:
            session["user"] = username
            session["user_id"] = user["id"]
            return redirect("/")
        return "Invalid username or password"

    return render_template("login.html")


@app.route("/create_post", methods=["GET", "POST"])
def create_post():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        user_id = session.get("user_id")

        if not user_id:
            user_id = get_user_id(session["user"])

        conn = get_posts_db()
        conn.execute("INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
                     (user_id, title, content))
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("create_post.html")


@app.route("/edit_post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    user_id = session["user_id"]
    conn = get_posts_db()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()

    if not post or post["user_id"] != user_id:
        conn.close()
        return "You can't edit this post", 403

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        conn.execute("UPDATE posts SET title = ?, content = ? WHERE id = ?", 
                     (title, content, post_id))
        conn.commit()
        conn.close()
        return redirect("/")

    conn.close()
    return render_template("edit_post.html", post=post)


@app.route("/delete_post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    user_id = session["user_id"]
    conn = get_posts_db()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()

    if not post or post["user_id"] != user_id:
        conn.close()
        return "You can't delete this post", 403

    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/search")
def search():
   return render_template("search.html")

@app.route("/echo")
def echo():
    q = request.args.get("q", "")
    return f"You entered: {q}"


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
