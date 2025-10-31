from flask import Blueprint, request, redirect, session, jsonify
import requests
import os

auth_bp = Blueprint('auth', __name__)

# Discord OAuth2 configuration
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('BACKEND_URL') + '/auth/callback'
DISCORD_API_BASE = 'https://discord.com/api/v10'

@auth_bp.route('/discord')
def discord_auth():
    """Start Discord OAuth2 flow"""
    discord_oauth_url = (
        f"https://discord.com/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20guilds"
    )
    return redirect(discord_oauth_url)

@auth_bp.route('/callback')
def discord_callback():
    """Handle Discord OAuth2 callback"""
    code = request.args.get('code')
    
    if not code:
        return jsonify({"error": "No code provided"}), 400
    
    # Exchange code for access token
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_REDIRECT_URI,
        'scope': 'identify guilds'
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.post(f'{DISCORD_API_BASE}/oauth2/token', data=data, headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Failed to get access token"}), 400
    
    tokens = response.json()
    access_token = tokens['access_token']
    
    # Get user info
    user_headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    user_response = requests.get(f'{DISCORD_API_BASE}/users/@me', headers=user_headers)
    if user_response.status_code != 200:
        return jsonify({"error": "Failed to get user info"}), 400
    
    user_data = user_response.json()
    
    # Store user info in session
    session['user_id'] = user_data['id']
    session['username'] = user_data['username']
    session['avatar'] = user_data.get('avatar')
    session['access_token'] = access_token
    
    # Redirect to frontend
    frontend_url = os.getenv('FRONTEND_URL', 'https://your-frontend.netlify.app')
    return redirect(f"{frontend_url}/servers.html")

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return jsonify({"message": "Logged out successfully"})

@auth_bp.route('/user')
def get_user():
    """Get current user info"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    return jsonify({
        "id": session['user_id'],
        "username": session['username'],
        "avatar": session.get('avatar')
    })