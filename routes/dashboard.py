from flask import Blueprint, current_app, flash, redirect, render_template, request, session
from flask_mail import Mail, Message
from sqlalchemy import select

# Configure blueprint
blueprint = Blueprint("dashboard", __name__)
