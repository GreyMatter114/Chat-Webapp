from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
socketio = SocketIO(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


# Define the User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)


# Define the ChatRoom model
class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(10), unique=True, nullable=False)
    participants = db.relationship("User", secondary="participant", backref="chatrooms")


# Define the Participant model (for the many-to-many relationship)
participant = db.Table(
    "participant",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column(
        "chatroom_id", db.Integer, db.ForeignKey("chat_room.id"), primary_key=True
    ),
)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    return render_template("index.html", user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Login failed. Please check your username and password.", "error")
            redirect(url_for("register"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose another one.", "warning")
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created successfully! Please log in.", "info")
            return redirect(url_for("login"))
    return render_template("register.html")


@socketio.on("message")
@login_required
def handle_message(msg):
    emit("message", {"user": current_user.username, "msg": msg}, broadcast=True)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
