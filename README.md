# Coderr Backend

Coderr is a service marketplace. Providers publish offers with three package tiers. Customers book packages and review providers. This repository contains the Django REST API for the [Coderr frontend](https://github.com/Developer-Akademie-Backendkurs/project.Coderr).

## Local setup

Use Python 3.14 and Windows CMD. From the directory containing `manage.py`, create the virtual environment and install the pinned dependencies.

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

For a new installation, put the generated value in `DJANGO_SECRET_KEY` in `.env`. Set `DJANGO_DEBUG=True` for local development, `DJANGO_ALLOWED_HOSTS` to the local backend hostnames, and `DJANGO_CORS_ALLOWED_ORIGINS` to the frontend origins including scheme and port. The example allows Live Server on ports 5500 and 5501 on `127.0.0.1`.

```cmd
python manage.py migrate
python manage.py check
python manage.py runserver
```

The local API base URL is `http://127.0.0.1:8000/api`. Django uses SQLite for application data and the `media/` directory for uploaded files. To use [Django admin](http://127.0.0.1:8000/admin/), create a local administrator with `python manage.py createsuperuser`.

## API

| Area | Operations |
| --- | --- |
| Accounts and profiles | Register and log in, retrieve and edit profiles, list customers and providers. |
| Offers | Search, filter and order offers, read package details, create and manage provider-owned offers. |
| Orders | Book a package, list purchases or sales, change status as the associated provider, delete as staff and read provider order counts. |
| Reviews | Create one review per customer and provider pair, filter and sort reviews, edit or delete a review as its author. |
| Platform statistics | Read offer, provider and review counts and the average rating at `GET /api/base-info/`. |

Protected requests use `Authorization: Token <token>`. Registration and login return the token for the account.

## Tests and demo

Run the Django suite from the repository root. Django creates a separate test database.

```cmd
python manage.py test
```

For HTTP tests, follow the [Postman guide](postman/docs/README.md). It lists the matching environment, test scope and local inputs for each collection.

To try the customer and provider flows in the frontend, run `python manage.py seed_demo` against the migrated local database. It prepares both guest accounts and a bookable offer. See the [demo walkthrough](docs/DEMO_FLOW.md).
