#1
mkdir emv_api
cd emv_api


#2
# Create venv
python -m venv venv

# Activate (Windows CMD)
venv\Scripts\activate

# Activate (Windows PowerShell)
venv\Scripts\Activate.ps1

#3
pip install flask

#4
pip freeze > requirements.txt

#5 (run the project)
python app.py


#how to deploy Flask App on render
Deploying Your Flask EMV API to Render
STEP 1: Prepare Your Project Files
You need two extra files before deploying.
requirements.txt
flask
gunicorn

Note: Gunicorn is the production-grade server Render uses to run Flask. Never use Flask's built-in app.run() in production.

render.yaml (optional but recommended)
yamlservices:
  - type: web
    name: emv-api
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
Your final project structure should look like:
emv_api/
├── app.py
├── emv_parser.py
├── requirements.txt
├── render.yaml
└── venv/          ← NOT pushed to GitHub (add to .gitignore)
Create a .gitignore file:
venv/
__pycache__/
*.pyc
.env

STEP 2: Push to GitHub
bash# Inside your emv_api folder

git init
git add .
git commit -m "Initial commit - EMV Flask API"

# Create a new repo on GitHub first, then:
git remote add origin https://github.com/seniorman-dev/emv-api.git
git branch -M main
git push -u origin main

STEP 3: Deploy on Render

Go to render.com and sign up / log in
Click "New +" → select "Web Service"
Connect your GitHub account and select your emv-api repository
Fill in the settings:

FieldValueNameemv-apiRuntimePython 3Build Commandpip install -r requirements.txtStart Commandgunicorn app:appInstance TypeFree

Click "Create Web Service"

Render will build and deploy automatically. It takes about 2 minutes.

STEP 4: Update app.py for Production
Make sure your app.py bottom section looks like this:
pythonif __name__ == "__main__":
    # This only runs locally. Render uses gunicorn instead.
    app.run(debug=False, host="0.0.0.0", port=5000)

STEP 5: Get Your Live URL
Once deployed, Render gives you a URL like:
https://emv-api.onrender.com
Update your Flutter code accordingly:
dartstatic const String baseUrl = "https://emv-api.onrender.com";
Your endpoint becomes:
POST https://emv-api.onrender.com/emv/parse
Test it's live by hitting the health check in your browser:
https://emv-api.onrender.com/health
You should see:
json{ "status": "ok" }

STEP 6: Auto-Deploy on Every Push (Already Built Into Render)
Any time you push to your main branch:
bashgit add .
git commit -m "your update"
git push
Render automatically rebuilds and redeploys. No manual steps needed.
