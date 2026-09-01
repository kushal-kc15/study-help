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
| Deployment | DigitalOcean (planned) |

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

# Omit or leave empty to use SQLite locally when DEBUG=True
DATABASE_URL=

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

## Production Database

Production uses PostgreSQL through a provider-neutral `DATABASE_URL`. When
`DEBUG=False`, the setting is mandatory and must use a PostgreSQL URL. Local
development continues to use SQLite when `DEBUG=True` and `DATABASE_URL` is
empty.

Supply the production connection string through the hosting provider's
environment-variable or secrets interface. Do not commit it to the repository.

---

## Environment Variables

| Variable | Description | Required |
|---|---|---|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | `True` for dev, `False` for production | Yes |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | Yes |
| `DATABASE_URL` | PostgreSQL connection URL | Required when `DEBUG=False` |
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
├── render.yaml             # Legacy Render web-service config
├── Procfile
└── requirements.txt
```

---

## License

MIT
