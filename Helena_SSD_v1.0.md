# Helena — Rude Friend Chatbot
## Simple System Design Document (SSD)

| Field | Value |
|---|---|
| Version | 1.0 |
| Author | AOD (Akwasi Owusu-Duah) |
| Date | May 2026 |
| Status | Draft |

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Component Design](#3-component-design)
4. [Data Design](#4-data-design)
5. [UI / UX Design](#5-ui--ux-design)
6. [Deployment Architecture](#6-deployment-architecture)
7. [Constraints & Risks](#7-constraints--risks)
8. [Future Improvements](#8-future-improvements)
9. [Glossary](#9-glossary)

---

## 1. Project Overview

Helena is a web-based AI chatbot that simulates a rude, sarcastic, and chaotic friend. She is powered by the Google Gemini 2.5 Flash-Lite API and is designed for personal use among close friends. The name and personality are inspired by the developer's sister.

### 1.1 Objectives

- Deliver a fully functional AI chatbot with a distinct "full chaos" personality
- Keep each user's conversation history private and isolated from other users
- Implement a creative "knock to enter" interaction before the chat screen opens
- Deploy on AWS EC2 (Ubuntu) with a Python/Flask backend
- Keep the architecture simple, fast, and maintainable by a solo developer

### 1.2 Scope

**In scope:** Chat interface, knock screen, session-based memory (last 10 messages), Gemini API integration, Flask backend, EC2 deployment.

**Out of scope:** User accounts/login, persistent message history across sessions, mobile app, voice input.

---

## 2. System Architecture

### 2.1 Architecture Overview

Helena follows a simple two-tier client-server architecture. The frontend is a static HTML/CSS/JS single page served directly by Flask. The backend handles all Gemini API communication, keeping the API key server-side at all times.

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS EC2 (Ubuntu)                      │
│                                                              │
│   ┌─────────┐    ┌──────────┐    ┌───────────────────────┐  │
│   │  Nginx  │───▶│Gunicorn  │───▶│   Flask App (app.py)  │  │
│   │ :80/:443│    │  (WSGI)  │    │                       │  │
│   └─────────┘    └──────────┘    │  GET  /  → index.html │  │
│         ▲                        │  POST /chat → AI reply │  │
│         │                        └───────────┬───────────┘  │
│         │                                    │              │
│         │                                    ▼              │
│    User Browser                    ┌──────────────────┐     │
│   (HTML/CSS/JS)                    │  Session Store   │     │
│                                    │ { uuid: [...] }  │     │
│                                    └──────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
                              ┌──────────────────────────┐
                              │   Google Gemini API      │
                              │  gemini-2.5-flash-lite   │
                              └──────────────────────────┘
```

### 2.2 Tech Stack

| Layer | Component | Technology |
|---|---|---|
| Frontend | Knock screen + Chat UI | HTML / CSS / JS |
| Backend | API server + session manager | Python 3.x / Flask |
| AI Layer | Language model | Gemini 2.5 Flash-Lite API |
| Hosting | Cloud server | AWS EC2 (Ubuntu) |
| Process Manager | Keep Flask alive | Gunicorn + Systemd |
| Reverse Proxy | Handle HTTP traffic | Nginx |

### 2.3 Request Flow

```
User opens page
      │
      ▼
[Knock Screen shown]
      │
  User taps/clicks
      │
      ▼
[Knock animation plays ~800ms]
      │
      ▼
[Chat screen fades in]
[crypto.randomUUID() → session_id generated]
      │
  User types message → Send
      │
      ▼
POST /chat  { session_id, message }
      │
      ▼
Flask: fetch last 10 msgs for session_id
      │
      ▼
Flask: build prompt (system prompt + history + new message)
      │
      ▼
Gemini API call
      │
      ▼
Flask: append both messages to session history
      │
      ▼
Return { reply } to frontend
      │
      ▼
JS renders Helena's chat bubble
```

---

## 3. Component Design

### 3.1 Knock Screen (Frontend)

The knock screen is the first thing a user sees. It occupies the full viewport and instructs the user to tap/click to enter. A CSS animation simulates a door-knock effect on click. After the animation completes (~800ms), the knock screen fades out and the chat screen fades in. Fully achievable in plain HTML/CSS/JS — no React required.

**Behaviour:**
- Full-screen overlay with Helena's name and a "Knock" prompt
- Click/tap event listener triggers a CSS knock animation (scale + shake keyframes)
- After animation: knock screen gets `display:none`, chat screen gets `display:flex`
- `session_id` is generated via `crypto.randomUUID()` at this exact point

**CSS animation sketch:**
```css
@keyframes knock {
  0%   { transform: scale(1); }
  20%  { transform: scale(0.95) rotate(-2deg); }
  40%  { transform: scale(1.02) rotate(1deg); }
  60%  { transform: scale(0.97) rotate(-1deg); }
  80%  { transform: scale(1.01); }
  100% { transform: scale(1); }
}
```

---

### 3.2 Chat Interface (Frontend)

A clean, minimal chat UI with Tyrian Purple (`#66023C`) as the primary accent colour. Messages appear as chat bubbles — user messages on the right, Helena's on the left.

**Elements:**
- Chat bubble container with `overflow-y: scroll`
- User bubbles: right-aligned, light purple background (`#F5E6F0`)
- Helena bubbles: left-aligned, white background with Tyrian Purple accent border
- Input bar fixed at the bottom with a text input and Send button
- Typing indicator (animated dots) shown while waiting for Helena's response
- Auto-scroll to latest message on new bubble render

---

### 3.3 Flask Backend

A lightweight Python Flask application with two routes and an in-memory session store.

**Routes:**

| Method + Route | Purpose | Returns |
|---|---|---|
| `GET /` | Serve the HTML page | `index.html` |
| `POST /chat` | Process message + call Gemini | `{ "reply": string }` |

**Session memory:**

Session history is stored in a Python dictionary in server memory, keyed by `session_id`. Each entry holds a list of the last 10 message objects. When a new message arrives, it is appended and the list is trimmed to the last 10 entries. Simple, fast, no database needed. History is lost on server restart — acceptable for this use case.

```python
# In-memory session store
sessions = {}  # { "uuid": [ {role, parts}, ... ] }

MAX_HISTORY = 10

def get_history(session_id):
    return sessions.get(session_id, [])

def update_history(session_id, user_msg, model_reply):
    history = sessions.setdefault(session_id, [])
    history.append({"role": "user",  "parts": [{"text": user_msg}]})
    history.append({"role": "model", "parts": [{"text": model_reply}]})
    sessions[session_id] = history[-MAX_HISTORY:]
```

---

### 3.4 Helena's System Prompt

Helena's personality is defined entirely in the system prompt sent to Gemini on every request.

```
You are Helena. You are a rude, chaotic, unfiltered friend.

Rules:
- Roast both the question AND the person asking it
- Sometimes refuse to answer — claim you're busy even though you're doing nothing
- Complain loudly before answering (if you even answer)
- Never apologise, never soften your words
- Still give a real answer eventually — you're chaotic, not useless
- Short, punchy replies preferred. No essays.
```

---

### 3.5 Gemini API Integration

| Setting | Value | Reason |
|---|---|---|
| Model | `gemini-2.5-flash-lite` | Confirmed working on free tier |
| API key storage | `.env` file on server | Never exposed to frontend |
| Temperature | `1.8 – 2.0` | Maximise chaos and unpredictability |
| `max_output_tokens` | `512` | Enough for a rude reply; preserves quota |
| History format | `contents[]` array | Gemini API multi-turn format |

---

## 4. Data Design

### 4.1 Session Store Structure

```python
sessions = {
    "<uuid-v4>": [
        {"role": "user",  "parts": [{"text": "hey can you help me"}]},
        {"role": "model", "parts": [{"text": "Ugh. What now?"}]},
        # ... max 10 entries (5 turns)
    ]
}
```

### 4.2 POST /chat Request Payload

```json
{
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "message": "what is the weather today"
}
```

| Field | Type | Description |
|---|---|---|
| `session_id` | `string` (UUID v4) | Generated client-side at knock time |
| `message` | `string` | The user's typed message |

### 4.3 POST /chat Response Payload

```json
{
  "reply": "Why would I know the weather? I'm not your personal assistant. Google it yourself. ...Fine. It depends on where you are, genius."
}
```

### 4.4 Privacy Model

User isolation is achieved through the `session_id` UUID. Since IDs are generated client-side using `crypto.randomUUID()`, two users will always have different IDs. The server never links sessions to identities — there are no user accounts. Sufficient for a small, trusted-friends use case.

---

## 5. UI / UX Design

### 5.1 Colour Palette

| Name | Hex | Usage |
|---|---|---|
| Tyrian Purple | `#66023C` | Primary accent, Helena bubble border, header |
| Tyrian Light | `#F5E6F0` | User message bubble background |
| White | `#FFFFFF` | Helena bubble background, page bg |
| Dark Gray | `#1A1A1A` | Body text |
| Medium Gray | `#888888` | Timestamps, secondary text |

### 5.2 Screen States

| State | Description |
|---|---|
| **Knock screen** | Full viewport, centred text, click anywhere to proceed |
| **Chat screen** | Replaces knock screen, chat history + input bar visible |
| **Waiting** | Send button disabled, typing indicator shown |
| **Error** | API failure → Helena bubble shows a snarky error message |

### 5.3 Wireframes

See wireframe diagrams in the attached visual reference below.

---

## 6. Deployment Architecture

### 6.1 Server Stack on EC2

| Component | Role | Notes |
|---|---|---|
| Ubuntu (EC2) | Host OS | Existing instance |
| Python + Flask | Application server | Runs app logic |
| Gunicorn | WSGI server | Runs Flask in production |
| Nginx | Reverse proxy | Forwards port 80 → Gunicorn |
| Systemd | Process manager | Restarts Gunicorn on crash/reboot |
| `.env` file | Secret storage | Holds `GEMINI_API_KEY` |

### 6.2 Project File Structure

```
helena/
├── app.py                 # Flask app — routes + session logic
├── gemini.py              # Gemini API wrapper function
├── .env                   # GEMINI_API_KEY (never commit to git)
├── .gitignore             # includes .env
├── requirements.txt       # flask, google-generativeai, python-dotenv
├── templates/
│   └── index.html         # Full single-page UI
└── static/
    ├── style.css          # All styles
    └── app.js             # Knock logic + chat logic
```

### 6.3 Deployment Steps

1. SSH into EC2, clone repo, `cd helena/`
2. `pip install -r requirements.txt`
3. Create `.env` with `GEMINI_API_KEY=your_key`
4. Configure Gunicorn as a systemd service
5. Install and configure Nginx as reverse proxy on port 80
6. Open port 80 in EC2 Security Group inbound rules
7. Access via EC2 raw IP in browser

### 6.4 Nginx Config (minimal)

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 6.5 Systemd Service (minimal)

```ini
[Unit]
Description=Helena Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/helena
ExecStart=/usr/bin/gunicorn -w 2 -b 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 7. Constraints & Risks

| Risk | Description | Mitigation |
|---|---|---|
| Free tier quota | 1,500 req/day on Gemini free tier — shared across all sessions | Acceptable for small friend group; monitor usage |
| In-memory sessions | History lost on server restart | Acceptable for informal use; add Redis later if needed |
| No auth | Anyone with the IP can access Helena | Low risk — raw IP not publicly advertised |
| API key exposure | Key must never reach the browser | Stored in `.env`, only used server-side in Flask |
| Rate limiting | 15 RPM on free tier | Low risk given small user base |
| Gemini 503 errors | Server overload as seen during testing | Return a snarky Helena-style error message to user |

---

## 8. Future Improvements

- Add a simple PIN screen before the knock screen for light access control
- Persist session history in Redis so it survives server restarts
- Add a domain name + HTTPS via Let's Encrypt
- Let users adjust Helena's rudeness level (slider: "mildly annoying" → "full chaos")
- Add knock sound effects for extra drama
- Rate limiting per IP to protect free tier quota

---

## 9. Glossary

| Term | Definition |
|---|---|
| SSD | Simple System Design — a lightweight design doc for small projects |
| Flask | A lightweight Python web framework for building APIs and web apps |
| Gunicorn | A Python WSGI HTTP server that runs Flask apps in production |
| Nginx | A high-performance web server used here as a reverse proxy |
| Session ID | A UUID generated per user visit to isolate their conversation history |
| System Prompt | Instructions sent to the AI model that define Helena's personality |
| WSGI | Web Server Gateway Interface — the standard for Python web app servers |
| Gemini API | Google's AI API powering Helena's responses |
| EC2 | Amazon Elastic Compute Cloud — a virtual server on AWS |

---

*Helena SSD v1.0 — End of Document*
