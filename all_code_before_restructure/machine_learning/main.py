from flask import Flask
from chat import chat_bp

app = Flask(__name__)
app.register_blueprint(chat_bp, url_prefix="/api/chat")


@app.route("/")
def root():
    return {"message": "Bike chatbot backend is running"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
