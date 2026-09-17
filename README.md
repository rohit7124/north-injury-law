# Northstar Injury Law

A conversion-focused digital intake system built for personal injury law firms.

Northstar combines a professional law-firm website with structured case intake, lead management, response tracking, and intake performance measurement.

The system is intentionally focused on one operational workflow:

**Capture → Manage → Respond → Measure**

---

## What Northstar Does

A potential client visits the law firm's website and submits a case evaluation form.

The submission flows into an internal Lead Desk where the firm can:

- Review potential cases
- Search and filter leads
- View structured case information
- Track lead status
- Add internal notes
- Record first-contact time
- Measure response time
- Monitor the current intake pipeline

### Lead workflow

```text
Potential Client
       ↓
Law Firm Website
       ↓
Case Evaluation Form
       ↓
FastAPI Backend
       ↓
SQLite Database
       ↓
Northstar Lead Desk
       ↓
New → Contacted → Qualified
       ↓
Retained / Closed / Lost
Core Features
1. Professional PI Website

A responsive personal injury law-firm website designed around trust, clarity, and conversion.

Includes:

Practice-area content
Case evaluation CTA
FAQ section
Responsive navigation
Mobile-friendly layout
Structured intake form
Form validation
Success and error states
2. Structured Case Intake

The case evaluation form collects structured information including:

First and last name
Phone
Email
Preferred contact method
Accident type
Accident date
Description of what happened
Consent

The frontend sends submissions to the FastAPI backend through a JSON API.

3. Lead Desk

The internal dashboard provides a lightweight workspace for managing potential cases.

Features include:

Total lead count
New leads
Contacted leads
Qualified leads
Retained leads
Search
Status filtering
Lead detail view
Internal notes
Responsive dashboard layout

Supported statuses:

new
contacted
qualified
retained
closed
lost
4. Response Tracking

Northstar records the first time a lead is moved from New to Contacted.

The dashboard can then show:

First Contact
Response Time
Leads still awaiting contact

The original first-contact timestamp is preserved as the lead progresses through later statuses.

5. Intake Performance

The dashboard includes a focused measurement layer for intake operations.

Current metrics include:

Average Response Time
Awaiting Contact
Lead → Retained

The Lead → Retained metric represents the current snapshot of leads whose present status is retained.

Architecture
Website
   │
   │ HTTP / JSON
   ▼
FastAPI
   │
   ├── Pydantic validation
   ├── Lead API
   ├── Status updates
   └── Admin API-key protection
   │
   ▼
SQLite
   │
   └── leads.db

Lead Desk
   │
   └── Reads and updates leads through the API
Project Structure
new law/
│
├── index.html
├── styles.css
├── script.js
│
├── main.py
├── database.py
├── models.py
├── notifications.py
│
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── northstar web/
│   ├── index.html
│   ├── styles.css
│   └── script.js
│
└── northstar dashboard/
    └── index.html

The northstar dashboard/index.html file contains the dashboard HTML, CSS, and JavaScript in one file.

API
Health Check
GET /api/health

Returns the backend health status.

Create Lead
POST /api/leads

Creates a new potential-client lead.

List Leads
GET /api/leads

Returns stored leads.

This endpoint requires the configured admin API key.

Update Lead Status
PATCH /api/leads/{lead_id}/status

Updates the status of a lead.

Update Internal Notes
PATCH /api/leads/{lead_id}/notes

Updates the internal notes associated with a lead.

Run Locally
Backend

From the project root:

.\.venv\Scripts\activate
python -m uvicorn main:app --reload

The API runs at:

http://127.0.0.1:8000

Health check:

http://127.0.0.1:8000/api/health
Website

Open a second terminal:

python -m http.server 8080

Open:

http://localhost:8080
Lead Desk

Open a third terminal:

cd "C:\Users\Rohit Paikrao\Downloads\new law\northstar dashboard"
python -m http.server 8081

Open:

http://localhost:8081
Environment Variables

Create a local .env file using .env.example as the template.

Example:

ADMIN_API_KEY=your-local-admin-key

ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://localhost:8081,http://127.0.0.1:8081

Optional email notification settings can also be configured through environment variables.

Never commit .env or real credentials to GitHub.

The repository includes .env.example instead.

Local Data

Lead records are stored in:

leads.db

The database is created automatically when the backend starts.

leads.db is intentionally excluded from Git through .gitignore.

Deployment

The frontend is static and can be hosted on a static hosting platform such as Netlify.

The FastAPI backend must be deployed separately to infrastructure capable of running a persistent Python application.

The local development configuration should not be used for handling real client information in production.

Security & Production Considerations

This repository is a working prototype and demonstration system.

Before a real law firm uses the system with real prospective-client information, additional safeguards should be implemented, including:

HTTPS
Production-grade authentication
Secure secret management
Rate limiting
Spam and abuse protection
Production database infrastructure
Appropriate database access controls
Data retention policies
Monitoring and logging
Privacy and compliance review
Appropriate legal and ethical review

The local admin API key is intended for development/demo use and is not production authentication.

Product Philosophy

Northstar is intentionally focused rather than feature-heavy.

The system concentrates on the operational path between a potential client submitting an inquiry and the firm acting on that opportunity:

Capture
   ↓
Manage
   ↓
Respond
   ↓
Measure

AI-assisted capabilities can be added later where they provide a clear operational benefit.

Status

Prototype / V1

Current V1 capabilities:

Professional PI website
Structured case intake
Lead management
Lead status workflow
Internal notes
First-contact tracking
Response-time measurement
Intake performance measurement
Disclaimer

Northstar Injury Law is a fictional demonstration concept.

This project is not a real law firm, does not provide legal advice, and does not create an attorney-client relationship.

Any names, testimonials, case results, phone numbers, or other firm information shown in the demonstration are fictional.
