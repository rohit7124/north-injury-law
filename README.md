# Northstar Injury Law — Lead Capture System

A static marketing site (HTML/CSS/JS) with a small FastAPI + SQLite backend
for the case-evaluation form. Built as an MVP: no ORM, no auth framework,
no build step on the frontend.

## Project structure

```
/
├── index.html            Site markup (unchanged design, real form wiring)
├── styles.css            Site styles (unchanged design + 3 targeted bug fixes)
├── script.js             Site behavior: nav, FAQ, and the real submission flow
├── backend/
│   ├── main.py           FastAPI app: POST /api/leads, GET /api/leads, /api/health
│   ├── database.py       SQLite persistence (stdlib sqlite3, no ORM)
│   ├── models.py         Request validation (Pydantic)
│   └── notifications.py  Best-effort email notification on new leads
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 1. What changed, and why

**Bug fixes (found via testing, not just read):**

1. **Mobile horizontal-scroll bug.** The off-canvas mobile nav panel
   (`position: fixed` + `translateX(100%)`) was enlarging the page's
   scrollable width at 320–390px viewports, even though `overflow-x: hidden`
   was set on `<body>`. Fixed by adding `overflow-x: hidden` to `<html>`
   as well, and making the closed panel `visibility: hidden` so it can't
   affect layout or be tabbed into while off-screen.
2. **Header CTA crowding.** At ≤400px, the logo + "Free Case Evaluation"
   button + hamburger icon didn't reliably fit on one line. The header CTA
   is now hidden below 400px (the same CTA remains one tap away in the menu
   and is repeated throughout the page).
3. **Nav-panel offset was a hardcoded `78px`.** If the header ever wrapped
   to a second line, the mobile nav panel would open at the wrong position.
   JS now measures the real header height and exposes it as a CSS variable
   (`--header-h`), so the panel always sits exactly below the header.
4. **Layout-shift bug in form validation.** Fixing a field's error and
   immediately interacting with the control right below it (e.g. the
   consent checkbox) caused the error text to collapse at that exact
   instant, shifting the page ~20px under the pointer. Fixed by clearing
   errors live as soon as a field becomes valid (not only on blur) and by
   reserving fixed height for error text so it never collapses.
5. **The success message was visible on every fresh page load.** A CSS rule
   (`.form-success { display: flex }`) was silently overriding the `hidden`
   attribute — in CSS, an author stylesheet's `display` declaration beats
   the browser's default `[hidden] { display: none }` rule regardless of
   selector specificity. This meant "Thank you, your request has been
   received" was sitting on the page before anyone submitted anything.
   Fixed with an explicit `.form-success[hidden] { display: none }` rule.

**Frontend form behavior:**
- Added an "Accident date" field (optional).
- Removed all "this is a demo" messaging and the demo success text.
- Submit button now disables and reads "Submitting…" during the request.
- Real `fetch()` call to `POST /api/leads`; handles success, validation
  errors (mapped back to the specific field), and network/server failures
  with the exact messages you specified.

**Backend:** built from scratch (previously none) — see architecture below.

---

## 2. How frontend, API, and database communicate

```
Browser (index.html/script.js)
   │  fetch(`${API_BASE}/api/leads`, { method: "POST", body: JSON })
   ▼
FastAPI (backend/main.py)
   │  Pydantic validates the payload (backend/models.py)
   │  → 422 with field errors if invalid
   ▼
SQLite (backend/database.py → backend/leads.db)
   │  INSERT, then main.py attempts an email notification
   │  (backend/notifications.py — best-effort, never blocks the response)
   ▼
JSON response → browser shows the real success or error state
```

`API_BASE` is set in a small inline `<script>` block in `index.html`,
right before `script.js` loads:

```html
<script>
  window.NORTHSTAR_API_BASE = "http://localhost:8000";
</script>
```

This is a public URL, not a secret — change it to your deployed backend's
URL when you deploy (see §5).

---

## 3. Run it locally

**Backend:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r ../requirements.txt
cp ../.env.example .env          # edit .env if you want email notifications
uvicorn main:app --reload --port 8000
```
You should see `Database ready. Allowed CORS origins: [...]` in the log,
and `backend/leads.db` will be created automatically on first run.

Verify it's up:
```bash
curl http://localhost:8000/api/health
# {"status":"ok"}
```

**Frontend**, in a second terminal:
```bash
python3 -m http.server 8080
```
Visit `http://localhost:8080`. With both running, submitting the form on
`localhost:8080` will hit the API on `localhost:8000` (already the default
in `index.html` and in `.env.example`'s `ALLOWED_ORIGINS`).

---

## 4. Deploying the backend and connecting it to Netlify

Netlify serves static files — it cannot run a persistent Python/uvicorn
process. **Deploy the FastAPI backend separately**, on a host built for
long-running processes (Render, Railway, Fly.io, a small VPS, etc. — all
work fine for this app; pick whichever you're already comfortable with).
That's the correct architecture here: SQLite needs a writable, persistent
filesystem attached to one running process, which rules out Netlify
Functions (stateless, ephemeral, no persistent disk — you'd need to swap
SQLite for a hosted database to use Functions, which is unnecessary for
an MVP at this scale).

Steps:
1. Deploy the `backend/` folder to your chosen host. Typical start command:
   `uvicorn main:app --host 0.0.0.0 --port $PORT`
2. Set the environment variables from `.env.example` on that host
   (most hosts have an "Environment Variables" panel — don't commit `.env`).
   Set `ALLOWED_ORIGINS` to your real Netlify URL, e.g.
   `https://northstar-injury-law.netlify.app`.
3. In `index.html`, change:
   ```html
   window.NORTHSTAR_API_BASE = "https://your-backend-host.example.com";
   ```
4. Redeploy the frontend to Netlify as usual (it's still just static files).

---

## 5. Environment variables

| Variable | Required? | Purpose |
|---|---|---|
| `ALLOWED_ORIGINS` | Recommended | Comma-separated origins allowed to call the API (CORS). Defaults to `http://localhost:8000,http://127.0.0.1:8000` if unset. |
| `NOTIFICATION_EMAIL` | Optional | Where new-lead emails are sent. |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` | Optional | SMTP credentials for sending that email. If any is missing, email sending is skipped — leads are still saved. |
| `ADMIN_API_KEY` | Optional | Enables `GET /api/leads` (send it as an `X-API-Key` header) so you can see stored leads. Leave blank to disable that endpoint entirely. |

---

## 6. Testing a lead from your phone

1. Make sure your phone is on the same Wi-Fi network as your computer.
2. Find your computer's local IP (e.g. `192.168.1.42`):
   - macOS: `ipconfig getifaddr en0`
   - Linux: `hostname -I`
   - Windows: `ipconfig` (look for IPv4 Address)
3. Start the backend with `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
   (the `--host 0.0.0.0` is what makes it reachable from another device).
4. Temporarily set, in `index.html`:
   ```html
   window.NORTHSTAR_API_BASE = "http://192.168.1.42:8000";
   ```
   and add `http://192.168.1.42:8080` to `ALLOWED_ORIGINS` in `.env`.
5. Serve the frontend with `python3 -m http.server 8080`.
6. On your phone's browser, go to `http://192.168.1.42:8080`.

---

## 7. What's verified vs. what still needs checking on your machine

I'm being specific here rather than just saying "tested":

**Genuinely tested, with real tools, in this environment:**
- **Frontend, in a real headless Chromium (Playwright):** mobile nav at
  320/375/390px (including actual sideways-scroll attempts, not just a
  metric check), desktop nav, FAQ accordion, empty/invalid-field
  validation, a full successful submission (with the API mocked at the
  network layer), backend-unavailable handling, and 422 field-error
  mapping. 46/46 checks passed after fixing the 5 bugs listed in §1.
- **`database.py`:** exercised directly against a real SQLite file —
  inserts, optional-field nulls, ordering, defaults.
- **`models.py`, `notifications.py`, `main.py`:** this sandbox has no
  network access, so `pip install fastapi/pydantic` isn't possible here
  (confirmed — the install fails with "no matching distribution found",
  not just "I didn't try"). To still genuinely execute these files rather
  than only read them, I wrote a small offline stand-in for the pydantic/
  FastAPI APIs and ran the real, unmodified files through it: 26 checks
  covering valid/invalid payloads for every field, the DB insert path, the
  notification skip-path and failure-path (real `smtplib`, a real refused
  connection), and the admin-key gating logic. All passed.

**Not yet tested, because it requires the real packages and a real HTTP
server, neither available in this sandbox — please verify on your machine:**
- Actually running `uvicorn main:app` and hitting it with real HTTP
  requests (request parsing, real CORS headers on the wire, real status
  codes).
- The exact wording/format of FastAPI's real 422 validation responses
  (my stand-in approximates pydantic v2's shape but isn't pydantic itself).
- Sending a real notification email through real SMTP credentials.
- The full flow end-to-end through your actual deployed backend URL.

The commands in §3 will let you confirm all of the above in a few minutes
once you're on a machine with internet access.

---

## 8. Security, privacy, and compliance — before real client data touches this

This is explicitly an MVP. Before a real law firm uses this with real
prospective clients, at minimum:

- **Transport security:** deploy the backend behind HTTPS only (most hosts
  do this by default, but confirm it) — this form collects names, phone
  numbers, and descriptions of injuries.
- **Data at rest:** SQLite here is a single unencrypted file. For real
  client data, consider disk-level encryption at minimum, and a managed
  database with proper backups and access controls for anything beyond a
  short pilot.
- **Access control:** the `ADMIN_API_KEY` header is a shared secret, not a
  real authentication system — no per-user accounts, no audit log of who
  viewed what. Replace with real authentication before more than one
  trusted person needs access.
- **Rate limiting / abuse protection:** there is currently none. A public
  POST endpoint with no rate limit is exposed to spam and scripted abuse.
  Add rate limiting (e.g. by IP) and consider a CAPTCHA if abuse becomes an
  issue.
- **Data retention policy:** nothing here defines how long leads are
  retained or how they're deleted. A real firm needs an explicit policy,
  consistent with applicable state bar and privacy rules.
- **Legal/ethical review:** the consent checkbox text, the "no fee unless
  we recover" language, and the intake questions themselves should be
  reviewed by the firm's own counsel before real use — this is a technical
  build, not a legal compliance review.
- **Logging hygiene:** `main.py` deliberately avoids logging lead details
  on failure (only that a failure happened), but review your hosting
  provider's own request/access logs too, since those can capture more
  than you intend by default.

None of this is implemented — it's flagged so you know what's still
missing before treating this as more than a demo/pilot.
