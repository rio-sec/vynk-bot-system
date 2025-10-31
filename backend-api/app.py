from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
from dotenv import load_dotenv
from auth import auth_bp
from routes import api_bp
from database import init_db

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# CORS configuration
CORS(app, origins=[os.getenv('FRONTEND_URL', 'https://your-frontend.netlify.app')], 
     supports_credentials=True)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(api_bp, url_prefix='/api')

# Initialize database
init_db()

@app.route('/')
def home():
    return jsonify({"message": "VYNK Backend API", "status": "running"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('DEBUG', False))