from flask import Blueprint, render_template, request, session, current_app
import requests

main = Blueprint('main', __name__)

MODEL_NAME = "deepseek/deepseek-r1-0528:free"

@main.route('/', methods=['GET', 'POST'])
def index():
    if 'history' not in session:
        session['history'] = []

    error = None
    if request.method == 'POST':
        prompt = request.form.get('user_input')
        if prompt:
            # Add user message to history
            session['history'].append({"role": "user", "content": prompt})
            session.modified = True

            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {current_app.config['OPENROUTER_API_KEY']}",
                "Content-Type": "application/json"
            }
            data = {
                "model": MODEL_NAME,
                "messages": session['history']
            }
            
            try:
                res = requests.post(url, headers=headers, json=data, timeout=120)
                if res.status_code == 200:
                    ai_content = res.json()["choices"][0]["message"]["content"]
                    session['history'].append({"role": "assistant", "content": ai_content})
                    session.modified = True
                else:
                    error = f"API Error {res.status_code}: {res.text}"
            except Exception as e:
                error = f"Connection failed: {str(e)}"

    return render_template("index.html", history=session.get('history', []), error=error)
