from flask import Flask
from flask_mail import Mail
from flask_session import Session
from os import environ

from database import db
from helpers import scheduler, socketio
from routes import dashboard, general, sockets

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    """Add and edit headers so responses aren't cached."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL").replace("postgres", "postgresql")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure email
app.config["MAIL_USERNAME"] = environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = environ.get("MAIL_PASSWORD")
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
mail = Mail(app)

# Configure scheduler
app.config["SCHEDULER_API_ENABLED"] = False
scheduler.init_app(app)
scheduler.start()

# Configure sockets
socketio.init_app(app)

# Configure custom variables
app.config["AVATAR_FOLDER"] = "static/images/avatars"
app.config["DOMAIN_URL"] = "http://127.0.0.1"
app.config["GITHUB_LINK"] = "https://github.com/jianmin-chen/officehours"

# Configure routes
app.register_blueprint(dashboard.blueprint)
app.register_blueprint(general.blueprint)
app.register_blueprint(sockets.blueprint)

if __name__ == "__main__":
    socketio.run(app)
