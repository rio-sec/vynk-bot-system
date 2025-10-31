from flask import Blueprint, request, jsonify, session
import requests
import os
from database import get_db_connection

api_bp = Blueprint('api', __name__)
DISCORD_API_BASE = 'https://discord.com/api/v10'

@api_bp.route('/servers')
def get_servers():
    """Get user's servers where bot is present and user has admin permissions"""
    if 'access_token' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    headers = {
        'Authorization': f'Bearer {session["access_token"]}'
    }
    
    # Get user's guilds
    response = requests.get(f'{DISCORD_API_BASE}/users/@me/guilds', headers=headers)
    if response.status_code != 200:
        return jsonify({"error": "Failed to get servers"}), 400
    
    user_guilds = response.json()
    
    # Get bot's guilds from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM servers")
    bot_guilds = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    
    # Filter guilds where bot is present and user has admin
    accessible_guilds = []
    for guild in user_guilds:
        if guild['id'] in bot_guilds and (int(guild['permissions']) & 0x8):  # ADMIN permission
            accessible_guilds.append({
                'id': guild['id'],
                'name': guild['name'],
                'icon': guild.get('icon'),
                'owner': guild['owner']
            })
    
    return jsonify(accessible_guilds)

@api_bp.route('/server/<server_id>/config')
def get_server_config(server_id):
    """Get server configuration"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT verified_role_id, log_channel_id, welcome_message FROM servers WHERE id = ?",
        (server_id,)
    )
    config = cursor.fetchone()
    conn.close()
    
    if not config:
        return jsonify({"error": "Server not found"}), 404
    
    return jsonify({
        "verified_role_id": config[0],
        "log_channel_id": config[1],
        "welcome_message": config[2]
    })

@api_bp.route('/server/<server_id>/config', methods=['POST'])
def update_server_config(server_id):
    """Update server configuration"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE servers SET 
           verified_role_id = ?, 
           log_channel_id = ?, 
           welcome_message = ? 
           WHERE id = ?""",
        (data.get('verified_role_id'), data.get('log_channel_id'), 
         data.get('welcome_message'), server_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Configuration updated successfully"})

@api_bp.route('/server/<server_id>/verify', methods=['POST'])
def process_verification(server_id):
    """Process user verification"""
    data = request.json
    user_id = data.get('user_id')
    user_ip = request.remote_addr
    
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    # Get verified role from database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT verified_role_id FROM servers WHERE id = ?",
        (server_id,)
    )
    server_config = cursor.fetchone()
    
    if not server_config or not server_config[0]:
        conn.close()
        return jsonify({"error": "Server not configured for verification"}), 400
    
    # Log verification
    cursor.execute(
        "INSERT INTO verification_logs (server_id, user_id, user_ip) VALUES (?, ?, ?)",
        (server_id, user_id, user_ip)
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        "message": "Verification successful",
        "role_id": server_config[0]
    })

@api_bp.route('/server/<server_id>/logs')
def get_verification_logs(server_id):
    """Get verification logs for server"""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT user_id, user_ip, verified_at 
           FROM verification_logs 
           WHERE server_id = ? 
           ORDER BY verified_at DESC LIMIT 100""",
        (server_id,)
    )
    logs = cursor.fetchall()
    conn.close()
    
    log_list = []
    for log in logs:
        log_list.append({
            "user_id": log[0],
            "user_ip": log[1],
            "verified_at": log[2]
        })
    
    return jsonify(log_list)