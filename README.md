# Coderr Backend

Django REST Framework backend for the Coderr training project at
Developer Akademie.

This repository contains the backend only. Development is in progress.

## Current implementation

- Django project configuration in `core`
- SQLite database
- Environment-based settings
- DRF token authentication configured
- CORS configured for the local frontend
- Django administration
- Basic user profile model
- Five automated profile model tests

Registration, login and the remaining business API endpoints are not
implemented yet.

## Requirements

- Python 3.14
- Git
- Windows CMD for the commands below

Development currently uses Python 3.14.3.
Exact package versions are listed in `requirements.txt`.

## Local setup

Download or clone this backend repository and open CMD in its root
directory, which contains `manage.py`.

Create and activate a virtual environment:

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

Install the dependencies:

```bat
python -m pip install -r requirements.txt
python -m pip check
```

Create your local environment file:

```bat
copy .env.example .env
```

Run this copy command only when setting up a new environment.
Do not overwrite an existing `.env` containing your local settings.

Generate a secret key:

```bat
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated value into `DJANGO_SECRET_KEY` in `.env`.
Keep the surrounding single quotes and never commit the real key.

The environment variables are:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Secret key used by Django |
| `DJANGO_DEBUG` | Local debugging; use `True` for development |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated backend hostnames |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins |

Check the configuration and apply migrations:

```bat
python manage.py check
python manage.py migrate
```

Create a local administrator:

```bat
python manage.py createsuperuser
```

Start the development server:

```bat
python manage.py runserver
```

Open the administration interface:

http://127.0.0.1:8000/admin/

The development server is intended for local development only.

## Frontend

The provided frontend is maintained separately:

https://github.com/Developer-Akademie-Backendkurs/project.Coderr

The current local frontend origin is:

```text
http://127.0.0.1:5500
```

CORS applies to paths beginning with `/api/`.
The origin must match the browser address, including protocol, hostname
and port. Do not include a page path such as `/index.html`.

CORS configuration alone does not implement API endpoints.
Full frontend integration is still pending.

## Tests

Run all tests:

```bat
python manage.py test
```

Run the accounts tests with detailed output:

```bat
python manage.py test accounts_app --verbosity 2
```

Django creates a separate test database. These tests do not modify the
local development database or its administrator account.

The current model tests cover:

- Linking a customer profile to its user
- An initially empty profile upload timestamp
- Empty strings for optional profile text fields
- At most one profile per user
- Deleting a user's profile with that user while preserving other accounts

Postman collection and environment files will be added during API
development. They are not available yet.

## Project structure

```text
accounts_app/
    api/
    migrations/
    admin.py
    apps.py
    models.py
    tests.py
    views.py
core/
    settings.py
    urls.py
    asgi.py
    wsgi.py
manage.py
requirements.txt
.env.example
.gitignore
```

API implementations will be placed inside each app's `api` directory.
The generated `accounts_app/views.py` is currently unused.

## Local files and version control

The following remain local and must not be committed:

- `.env`
- `.venv/`
- `db.sqlite3` and its temporary files
- Uploaded files in `media/`
- Collected static files in `staticfiles/`

Migration files and `requirements.txt` belong in version control.

Media paths are configured, but profile image uploads and development
media serving are not implemented yet.