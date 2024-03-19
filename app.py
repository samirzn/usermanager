from flask import Flask, render_template, request, redirect, url_for, session
import json
from datetime import datetime, timedelta
import requests
import threading
import time
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure random value

# Load users from a plain text file
def load_users():
    try:
        with open('users.txt', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save users to a plain text file
def save_users(users):
    with open('users.txt', 'w') as file:
        json.dump(users, file)

# Send a message to Telegram bot
def send_telegram_message(username, servername, expiry_date):
    bot_token = '6459343532:AAEukUlQbdvgg5eHgIOduSdgtkzfv0L1pMo'
    chat_id = '6012569599'
    message = f"User {username} on server {servername} has expired on {expiry_date}. Please take action."
    requests.get(f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}")

# Check for expired users and send notifications
def check_expired_users():
    while True:
        users = load_users()
        current_date = datetime.now()

        for user_id, user in users.items():
            expiry_date = datetime.strptime(user['expiry_date'], '%Y-%m-%d')
            user['expired'] = expiry_date <= current_date

        users = {user_id: user for user_id, user in sorted(users.items(), key=lambda x: x[1]['expired'], reverse=True)}

        for user_id, user in users.items():
            if user['expired']:
                send_telegram_message(user['username'], user['servername'], user['expiry_date'])

        save_users(users)
        time.sleep(20)  # Sleep for 20 seconds before checking again

# Home route to display users
@app.route('/')
def home():
    users = load_users()
    return render_template('index.html', users=users, session=session)

# Add user route
@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    servername = request.form['servername']
    expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d')

    users = load_users()
    if username in users.values():
        return render_template('duplicate_username.html')  # Prompt for duplicate username
    else:
        # Generate a unique identifier for the user
        user_id = str(uuid.uuid4())
        users[user_id] = {'username': username, 'servername': servername, 'expiry_date': expiry_date.strftime('%Y-%m-%d'), 'expired': False}
        save_users(users)
        return redirect(url_for('home'))

# Remove user route
@app.route('/remove_user/<user_id>')
def remove_user(user_id):
    users = load_users()
    users.pop(user_id, None)
    save_users(users)
    return redirect(url_for('home'))

# Edit user route
@app.route('/edit_user/<user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    users = load_users()
    if request.method == 'POST':
        username = request.form['username']
        servername = request.form['servername']
        expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d')
        
        users[user_id]['username'] = username
        users[user_id]['servername'] = servername
        users[user_id]['expiry_date'] = expiry_date.strftime('%Y-%m-%d')
        save_users(users)
        
        return redirect(url_for('home'))
    else:
        user = users.get(user_id)
        if user:
            user['user_id'] = user_id  # Include user_id in user dictionary for reference in the HTML template
            return render_template('edit_user.html', user=user)
        else:
            return 'User not found', 404
# Login route
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username == 'samir_zn' and password == 'love000':
        session['logged_in'] = True
        session.permanent = True  # Set the session to expire after a certain time (configurable)
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    # Start the thread to check for expired users
    expiration_thread = threading.Thread(target=check_expired_users)
    expiration_thread.start()

    # Run the Flask app
    app.run(debug=True,  host='0.0.0.0', port=80)
