# StudyHelp

A real-time collaborative study platform where students find study rooms, join discussions, and connect with peers around the world.

![Django](https://img.shields.io/badge/Django-6.0-092E20?style=flat&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat&logo=postgresql&logoColor=white)
![WebSockets](https://img.shields.io/badge/WebSockets-Daphne-FF6B6B?style=flat)

---

## Features

- **Study Rooms** — Create or join topic-based rooms. Join gate before participating.
- **Real-time Chat** — Live messaging via Django Channels WebSockets with typing indicators.
- **Direct Messages** — Private conversations between users with unread badge.
- **Notifications** — Bell dropdown with recent notifications, separate DM badge.
- **Smart Feed** — Personalised "For You" tab based on interests, plus Trending, New, Joined, and All tabs.
- **File Sharing** — Upload images, PDFs, code files, and ZIPs inside rooms (drag & drop supported).
- **Emoji Reactions** — React to messages with 6 emoji reactions.
- **Message Search** — Full-text search within any room (Ctrl+F).
- **Infinite Scroll** — Older messages load automatically as you scroll up.
- **User Profiles** — Bio, interests, badges, stats (rooms hosted, messages sent, joined since).
- **Badges** — Earned automatically: Newcomer, Verified, Room Host, Regular, Contributor, Popular, Sharer, Veteran.
- **Online Presence** — Green dot indicators showing who's currently online.
- **Bookmarks** — Save rooms for quick access.
- **Room Moderation** — Hosts can mute/unmute participants, kick users, pin messages, and manage invite links.
- **Google OAuth** — Sign in with Google alongside email/password auth.
- **Email Verification** — Verification email on registration.
- **Dark Mode** — System-aware, toggleable, persisted in localStorage.
- **Onboarding** — First-time user flow to set interests, goal, and level for personalised content.
- **Pagination** — Room list paginated with tab state preserved.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6, Django Channels, Daphne (ASGI) |
| Database | PostgreSQL (production), SQLite (development) |
| Real-time | WebSockets via Django Channels |
| Auth | Django auth + Social Auth (Google OAuth2) |
| Frontend | Vanilla JS, CSS custom properties, marked.js (Markdown) |
| Static files | WhiteNoise |
| Deployment | Render |

---

## Local Setup

**1. Clone the repo**
```bash
git clone https://github.com/kushal-kc15/study-help.git
cd study-help
```

**2. Create and activate a virtual environment**
```bash
python -m venv myvenv
# Windows
myvenv\Scripts\activate
# Mac/Linux
source myvenv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create a `.env` file**
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Leave these out to use SQLite locally
# DB_NAME=studyhelp
# DB_USER=postgres
# DB_PASSWORD=yourpassword
# DB_HOST=localhost
# DB_PORT=5432

# Google OAuth (optional for local dev)
GOOGLE_OAUTH2_KEY=your-google-client-id
GOOGLE_OAUTH2_SECRET=your-google-client-secret
```

**5. Run migrations and seed data**
```bash
python manage.py migrate
python manage.py seed          # 10 starter rooms
python manage.py seed_bulk     # 30 users, 30 rooms, 2000+ messages
```

**6. Create a superuser**
```bash
python manage.py createsuperuser
```

**7. Start the server**
```bash
python manage.py runserver
```

Visit `http://localhost:8000`

---

## Deployment (Render)

This project includes a `render.yaml` blueprint for one-click deployment.

1. Push your code to GitHub
2. Go to [render.com](https://render.com) → New → **Blueprint**
3. Connect your GitHub repo — Render will auto-configure the web service and PostgreSQL database
4. Set these environment variables manually in the Render dashboard:
   - `GOOGLE_OAUTH2_KEY`
   - `GOOGLE_OAUTH2_SECRET`
5. Update your Google OAuth Console with the Render callback URL:
   ```
   https://your-app.onrender.com/social-auth/complete/google-oauth2/
   ```

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | `True` for dev, `False` for production | Yes |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | Yes |
| `DB_NAME` | PostgreSQL database name | Production only |
| `DB_USER` | PostgreSQL user | Production only |
| `DB_PASSWORD` | PostgreSQL password | Production only |
| `DB_HOST` | PostgreSQL host | Production only |
| `DB_PORT` | PostgreSQL port (default: 5432) | Production only |
| `GOOGLE_OAUTH2_KEY` | Google OAuth2 client ID | Optional |
| `GOOGLE_OAUTH2_SECRET` | Google OAuth2 client secret | Optional |

---

## Project Structure

```
study-help/
├── base/                   # Main app
│   ├── management/
│   │   └── commands/
│   │       ├── seed.py         # Starter seed data
│   │       └── seed_bulk.py    # Bulk realistic seed data
│   ├── migrations/
│   ├── templates/base/     # App templates
│   ├── consumers.py        # WebSocket consumers
│   ├── models.py           # User, Room, Message, DM, Notification...
│   ├── views.py            # All views
│   ├── urls.py
│   ├── context_processors.py
│   └── pipeline.py         # Google OAuth pipeline
├── static/
│   ├── css/style.css
│   └── js/
│       ├── script.js       # Dark mode, dropdowns, notifications
│       └── presence.js     # Online status
├── studyhelp/
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py
├── templates/
│   ├── main.html           # Base layout
│   └── navbar.html
├── .env                    # Local env vars (not committed)
├── render.yaml             # Render deployment config
├── Procfile
└── requirements.txt
```

---

## License

MIT
