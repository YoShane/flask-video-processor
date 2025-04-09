from flask import Flask
from app.routes import main as main_blueprint
from app import app, socketio

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    app.register_blueprint(main_blueprint)

    return app

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)