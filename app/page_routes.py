from flask import Blueprint

pages = Blueprint("pages", __name__)

@pages.get("/")
def home():
    return "Dublin Bike Scheme App Running"
