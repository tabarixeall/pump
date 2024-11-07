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
    if request.method == 'POST':
        response = requests.post(url, headers=headers, data=request.data, cookies=request.cookies)
    elif request.method == 'PUT':
        response = requests.put(url, headers=headers, data=request.data, cookies=request.cookies)
    elif request.method == 'DELETE':
        response = requests.delete(url, headers=headers, cookies=request.cookies)
    else:
        response = requests.get(url, headers=headers, cookies=request.cookies)

    # Check if content type is HTML
    content_type = response.headers.get('Content-Type', '').lower()
    content = response.content

    # Inject JavaScript to handle mobile keyboard behavior
    if 'text/html' in content_type:
        injected_js = """
        <script>
            document.addEventListener('DOMContentLoaded', () => {
                const handleFocus = (event) => {
                    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                        setTimeout(() => {
                            event.target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            event.target.focus();
                        }, 200);
                    }
                };

                // Ensure focus event triggers for any new input fields as well
                const inputFields = document.querySelectorAll('input, textarea');
                inputFields.forEach(input => {
                    input.addEventListener('focus', handleFocus);
                    input.addEventListener('touchstart', handleFocus);
                });

                document.addEventListener('focusin', handleFocus);
                document.addEventListener('touchstart', handleFocus);

                // Dynamically handle any new inputs (in case of SPA content)
                const observer = new MutationObserver(() => {
                    const newInputFields = document.querySelectorAll('input, textarea');
                    newInputFields.forEach(input => {
                        input.addEventListener('focus', handleFocus);
                        input.addEventListener('touchstart', handleFocus);
                    });
                });
                observer.observe(document.body, { childList: true, subtree: true });
            });
        </script>
        """
        
        # Inject JavaScript before closing </body> tag
        content = content.decode('utf-8').replace('</body>', injected_js + '</body>')

    # Exclude specific headers that could cause issues
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for name, value in response.raw.headers.items() if name.lower() not in excluded_headers]

    # Log content for debugging if needed
    # Uncomment to log content and verify JavaScript is injected correctly
    # print(content)

    return Response(content, response.status_code, headers)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
