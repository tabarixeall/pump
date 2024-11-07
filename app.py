from flask import Flask, request, Response
import requests

app = Flask(__name__)

# Base URL of the site you want to proxy
BASE_URL = 'https://web.telegram.org/k/'

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    url = f"{BASE_URL}{path}"
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}

    # Handle different HTTP methods
    try:
        if request.method == 'POST':
            response = requests.post(url, headers=headers, data=request.data, cookies=request.cookies)
        elif request.method == 'PUT':
            response = requests.put(url, headers=headers, data=request.data, cookies=request.cookies)
        elif request.method == 'DELETE':
            response = requests.delete(url, headers=headers, cookies=request.cookies)
        else:
            response = requests.get(url, headers=headers, cookies=request.cookies)
    except requests.exceptions.RequestException as e:
        return f"Error during proxy request: {e}", 500

    # Inject JavaScript for mobile keyboard handling
    injected_js = """
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            // Ensure input fields are scrolled into view on focus
            document.addEventListener('focusin', (event) => {
                if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                    setTimeout(() => {
                        event.target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 200); // Delay to allow keyboard to appear
                }
            });

            // Observe changes in the DOM and re-apply the focus handler to new input fields
            const observer = new MutationObserver(() => {
                const inputFields = document.querySelectorAll('input, textarea');
                inputFields.forEach((input) => {
                    input.addEventListener('focus', () => {
                        setTimeout(() => {
                            input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }, 200);
                    });
                });
            });

            observer.observe(document.body, { childList: true, subtree: true });

            // Initialize the focus handler for existing input fields
            const inputFields = document.querySelectorAll('input, textarea');
            inputFields.forEach((input) => {
                input.addEventListener('focus', () => {
                    setTimeout(() => {
                        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 200);
                });
            });
        });
    </script>
    """

    # Inject JavaScript if the response is HTML content
    if 'text/html' in response.headers.get('Content-Type', ''):
        content = response.text.replace('</body>', injected_js + '</body>')
    else:
        content = response.content

    # Exclude specific headers that could cause issues with the proxy response
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for name, value in response.raw.headers.items() if name.lower() not in excluded_headers]
    
    return Response(content, response.status_code, headers)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
