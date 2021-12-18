from flask import Blueprint, current_app, flash, redirect, render_template, request, session
from flask_mail import Mail, Message
from sqlalchemy import select

# Configure blueprint
blueprint = Blueprint("general", __name__)


@blueprint.route("/")
def index():
    """Return main page or dashboard depending on whether user is logged in or not."""
    return render_template("index.html")


@blueprint.route("/signup", methods=["GET", "POST"])
def signup():
    """Route users use to sign up for an account."""
    if request.method == "GET":
        return render_template("account.html")

    return redirect("/")


@blueprint.route("/login", methods=["GET", "POST"])
def login():
    """Route users use to log into their account."""
    if request.method == "GET":
        return render_template("account.html")

    return redirect("/")
