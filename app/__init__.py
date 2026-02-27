from flask import Flask

def create_app():
    app = Flask(__name__)

    from .api_routes import api
    from .page_routes import pages

    app.register_blueprint(api)
    app.register_blueprint(pages)

    return app
