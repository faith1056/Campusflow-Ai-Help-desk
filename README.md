# CampusFlow AI Help Desk

A smarter way to investigate campus IT issues. CampusFlow is a Flask web app where you describe a problem, pick an AI provider, and get practical troubleshooting steps. Each request is saved as a ticket.

Live demo: https://campusflow-ai-help-desk.onrender.com

 The demo runs on Render's free tier. It sleeps after about 15 minutes of inactivity, so the first load can take up to a minute. Saved tickets may reset when the service restarts or redeploys.

 Features

- Dashboard with ticket statistics and AI provider status
- AI-powered troubleshooting from Google Gemini, Groq, or OpenRouter
- Ticket creation, saving, and a recent tickets table
- Command Center, an interactive in-app terminal
- Responsive dark interface

    Tech stack

- Python and Flask
- Gunicorn for production
- Gemini, Groq, and OpenRouter APIs
- HTML, CSS, and vanilla JavaScript
- JSON file storage (tickets.json)

 Project structure


Campusflow-Ai-Help-desk/
├── ai/                 # AI provider integrations
│   ├── ai_manager.py
│   ├── gemini.py
│   ├── groq.py
│   └── openrouter.py
├── static/
│   ├── css/style.css
│   └── js/app.js
├── storage/
│   └── tickets.py      # ticket saving and loading
├── templates/
│   └── index.html
├── tests/              # unit tests
├── app.py              # Flask application
├── main.py
├── requirements.txt
└── tickets.json


## Run locally

1. Clone the repository:
   
   git clone https://github.com/faith1056/Campusflow-Ai-Help-desk.git
   cd Campusflow-Ai-Help-desk
   

2. Create and activate a virtual environment:
   
   python -m venv .venv
   source .venv/bin/activate
   
   On Windows, use venv\Scripts\activate

3. Install dependencies:
   
   pip install -r requirements.txt
   

4. Create a  .env file in the project root with your API keys:
   
   GEMINI_API_KEY=your_key_here
   GROQ_API_KEY=your_key_here
   OPENROUTER_API_KEY=your_key_here
   
   Never commit this file. It is listed in gitignore

5. Start the app:
   
   python app.py
   
   Then open http://127.0.0.1:5000.

   Run the tests

python -m unittest discover tests


    Deploy to Render

1. Push the project to GitHub.
2. In Render, create a **New Web Service** and select this repository.
3. Use these settings:
   - **Build command:** pip install -r requirements.txt
   - **Start command:** gunicorn app:app
4. Under **Environment**, add GEMINI_API_KEY GROQ_API_KEY and OPENROUTER_API_KEY
5. Deploy. With Auto-Deploy set to On Commit, every push to main redeploys.

## Known limitations

- Tickets are stored in a JSON file, so they are lost when Render's free tier restarts the service. A database such as Postgres would fix this.
- The app has no login yet, so anyone with the link can use it.
- AI recommendations are suggestions, not verified diagnoses.

## Roadmap

- [ ] Password login
- [ ] Persistent database storage
- [ ] Ticket status updates (open, in progress, resolved)
- [ ] Favicon and further UI polish

## Author

Built by [faith1056](https://github.com/faith1056).