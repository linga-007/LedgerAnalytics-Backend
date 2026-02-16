from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
     
    from app.routes.upload import upload_bp
    app.register_blueprint(upload_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True , host='0.0.0.0', port=5000)
