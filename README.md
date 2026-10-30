# Job Portal

A Django web application that connects job seekers with employers. Employers can publish jobs and review applications; job seekers can search for roles and apply with a resume.

## Live demo

- Website: <https://job-portal-3lyx.onrender.com/>
- Django admin: <https://job-portal-3lyx.onrender.com/admin/> (login required)

Share reviewer login credentials privately. Never add admin passwords or database connection URLs to this README or the GitHub repository.

## Features

- Job seeker and employer registration, login, and role-specific dashboards.
- Job posting and job detail pages.
- Search and filters for keyword, location, and employment type.
- Applications with a required PDF, DOC, or DOCX resume (maximum 5 MB) and an optional cover letter.
- Employer application review, resume download, and status updates.
- Django admin for managing users, profiles, jobs, and applications.
- PostgreSQL for application data and WhiteNoise for production static files.

## Technology

- Python 3.12 or later
- Django 6.0
- PostgreSQL
- Gunicorn, WhiteNoise, and `dj-database-url` for deployment
- Django templates and CSS for the interface

## Run locally on Windows

### Requirements

- Python 3.12+
- PostgreSQL running locally

### 1. Open the project folder

Open a terminal in the folder containing `manage.py`.

### 2. Create and activate a virtual environment

In PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, open Command Prompt and run:

```cmd
.venv\Scripts\activate.bat
```

### 3. Install the project packages

```powershell
python -m pip install -r requirements.txt
```

### 4. Configure the local database

Copy the sample environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set `DB_NAME`, `DB_USER`, and `DB_PASSWORD` to match a PostgreSQL database and user that already exist on your computer. Keep this file private; it is ignored by Git.

If you have not created the local database and user yet, open `psql` as a PostgreSQL administrator and run the following, choosing your own password:

```sql
CREATE USER job_portal_user WITH PASSWORD 'choose-a-local-password';
CREATE DATABASE job_portal OWNER job_portal_user;
```

Use that same local password for `DB_PASSWORD` in `.env`.

Example local values:

```dotenv
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=
DB_NAME=job_portal
DB_USER=job_portal_user
DB_PASSWORD=your-local-postgres-password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Create the database tables

```powershell
python manage.py migrate
```

### 6. (Optional) Create a local Django admin account

```powershell
python manage.py createsuperuser
```

This account belongs to your **local** database. It is separate from any admin account created for the deployed site.

### 7. Start the development server

```powershell
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The Django admin is at <http://127.0.0.1:8000/admin/>.

## Test the project

Run the automated workflow tests with the included in-memory SQLite test settings:

```powershell
python manage.py test --settings=config.test_settings
```

This test configuration does not replace the PostgreSQL database used for normal local development or deployment.

## Deploy on Render

This project is configured for a Render web service and a Render PostgreSQL database.

### Web service commands

**Build command**

```text
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

**Start command**

```text
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

### Environment variables

Set these in the Render web service's **Environment** page:

| Name | Value |
| --- | --- |
| `DATABASE_URL` | Internal Database URL from the Render PostgreSQL database (web service and database should be in the same region) |
| `DJANGO_SECRET_KEY` | Generate a new secret in Render; never commit it |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | Render hostname only, e.g. `your-service.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Full HTTPS origin, e.g. `https://your-service.onrender.com` |

The project uses `SECURE_PROXY_SSL_HEADER` for Render's HTTPS proxy. Static files are collected during the build and served by WhiteNoise.

### Create a deployed admin account

The deployed admin account must be created in the **Render database**. On Render's free web-service plan, Shell access is unavailable, so from your local Windows Command Prompt you can temporarily point Django at the database's **External Database URL**:

```cmd
set "DATABASE_URL=PASTE_EXTERNAL_DATABASE_URL_HERE"
python manage.py createsuperuser
set DATABASE_URL=
```

Use a dedicated account for reviewers. Keep database URLs and admin passwords private. The deployed Django admin is at `https://your-service.onrender.com/admin/`.

## Data and uploaded resumes

- Local accounts, jobs, and applications are stored in your local PostgreSQL database. They do not automatically copy to Render.
- Deployed accounts, jobs, and applications are stored in the Render PostgreSQL database.
- Resume files are stored as uploaded media files, separately from PostgreSQL. Render's free web-service filesystem is temporary, so uploaded resumes can disappear after a restart or redeploy. Use dummy resumes for a free demo; configure persistent/object storage before relying on resume uploads long term.
- Render's free PostgreSQL database expires 30 days after creation. It is suitable for a short demo, not long-term production data. Check Render's current plan limits before deployment.

## Keep secrets and uploads out of Git

`.gitignore` excludes `.env`, `.venv`, local SQLite databases, and `media/`. Do not commit database passwords, production secret keys, connection URLs, or real resumes.

