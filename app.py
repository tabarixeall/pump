from flask import Flask, render_template_string

app = Flask(__name__)

# Simple form HTML with injected JavaScript for mobile keyboard handling
html_form = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Test Form</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        input, button {
            padding: 10px;
            font-size: 16px;
            margin-bottom: 20px;
            width: 100%;
        }
        button {
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>Simple Form Test</h1>
    <form action="#" method="post">
        <label for="name">Name:</label><br>
        <input type="text" id="name" name="name" placeholder="Enter your name" required><br>
        <button type="submit">Submit</button>
    </form>

    <script>
        // Injected JavaScript to handle keyboard behavior on mobile
        document.addEventListener('DOMContentLoaded', () => {
            const handleFocus = (event) => {
                if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
                    setTimeout(() => {
                        event.target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        event.target.focus();
                    }, 200);
                }
            };

            document.addEventListener('focusin', handleFocus);
            document.addEventListener('touchstart', handleFocus);

            // Dynamically apply handler to new input fields
            const observer = new MutationObserver(() => {
                const inputFields = document.querySelectorAll('input, textarea');
                inputFields.forEach((input) => {
                    input.addEventListener('focus', handleFocus);
                    input.addEventListener('touchstart', handleFocus);
                });
            });

            observer.observe(document.body, { childList: true, subtree: true });

            // Apply the handler to existing input fields
            const inputFields = document.querySelectorAll('input, textarea');
            inputFields.forEach((input) => {
                input.addEventListener('focus', handleFocus);
                input.addEventListener('touchstart', handleFocus);
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_form)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
