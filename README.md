 CampusFlow AI Help Desk

A smarter way to investigate campus IT issues. CampusFlow is a Flask web app where you describe a problem, pick an AI provider, and get practical troubleshooting steps. Each request is saved as a ticket.

Live demo:  https://campusflow-ai-help-desk.onrender.com

 The demo is password protected. It runs on Render's free tier, so it sleeps after about 15 minutes of inactivity and the first load can take up to a minute.

## Features

- Dashboard with ticket statistics and AI provider status
- AI-powered troubleshooting from Google Gemini, Groq, or OpenRouter
- Ticket creation and a recent tickets table
- Persistent ticket storage in PostgreSQL (Neon)
- Password login (HTTP Basic authentication)
- Command Center, an interactive in-app terminal
- Responsive dark interface
- Ticket detail view with full descriptions and AI suggestions
- Command Center `view T001` command
  Tech stack

- Python and Flask
- Gunicorn for production
- PostgreSQL on Neon, accessed with psycopg
- Gemini, Groq, and OpenRouter APIs
- HTML, CSS, and vanilla JavaScript

   Project structure


Campusflow-Ai-Help-desk/
├── ai/                  AI provider integrations
│   ├── ai_manager.py
│   ├── gemini.py
│   ├── groq.py
│   └── openrouter.py
├── static/
│   ├── css/style.css
│   └── js/app.js
├── storage/
│   └── tickets.py      # Postgres storage with a JSON file fallback
├── templates/
│   └── index.html
├── tests/              # unit tests
├── app.py              # Flask application and login
├── main.py
├── requirements.txt
└── tickets.json        # used only when DATABASE_URL is not set
```

   Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | Yes | Google Gemini access |
| `GROQ_API_KEY` | Yes | Groq access |
| `OPENROUTER_API_KEY` | Yes | OpenRouter access |
| `DATABASE_URL` | In production | Postgres connection string. If it is not set, tickets are saved to `tickets.json`. |
| `APP_USERNAME` | No | Login username (defaults to `admin`) |
| `APP_PASSWORD` | In production | Login password. If it is not set, the app has no login. |

Never commit real values. The `.env` file is listed in `gitignore`.

## Run locally

1. Clone the repository:
   
   git clone https://github.com/faith1056/Campusflow-Ai-Help-desk.git
   cd Campusflow-Ai-Help-desk


2. Create and activate a virtual environment:
   
   python -m venv .venv
   source .venv/bin/activate
   
   On Windows, use  .venv\Scripts\activate`.

3. Install dependencies:
   
   pip install -r requirements.txt
   

4. Create a  .env file in the project root:
   
   GEMINI_API_KEY=your_key_here
   GROQ_API_KEY=your_key_here
   OPENROUTER_API_KEY=your_key_here
   
   Leave out `DATABASE_URL` and `APP_PASSWORD` for local development. Tickets are then saved to `tickets.json` and no login is required.

5. Start the app:
   
   python app.py
   
   Then open http://127.0.0.1:5000.

## Run the tests
python -m unittest discover tests


The tests always use the JSON file and never touch the database.

## Deploy to Render

1. Push the project to GitHub.
2. Create a free Postgres database on [Neon](https://neon.tech) and copy its connection string. Neon's free database does not expire.
3. In Render, create a **New Web Service** and select this repository.
4. Use these settings:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
5. Under **Environment**, add `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `DATABASE_URL`, `APP_USERNAME`, and `APP_PASSWORD`.
6. Deploy. With Auto-Deploy set to On Commit, every push to `main` redeploys. The `tickets` table is created automatically on first use.

 Known limitations

- The login is one shared username and password, not per-user accounts.
- AI recommendations are suggestions, not verified diagnoses.- Ticket status tracking (Open, In progress, Resolved)


## Roadmap

- [x] Password login
- [x] Persistent database storage
- [x] Ticket status updates (open, in progress, resolved)
- [x] Favicon
- [ ] Delete tickets
- [ ] Ticket detail view with full AI suggestions
- [ ] Search and filter tickets
- [ ] Per-user accounts
- [x] Ticket detail view with full AI suggestions



## Author

Built by [faith1056](https://github.com/faith1056).


https://campusflow-ai-help-desk.onrender.com