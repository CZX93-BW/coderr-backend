# Coderr Backend

Coderr is a service marketplace built with Django REST Framework. Providers publish offers with three package tiers. Customers book a package at its current price and can review the provider. The [Coderr frontend](https://github.com/Developer-Akademie-Backendkurs/project.Coderr) uses this API for both customer and provider accounts.

**[Quickstart – run the backend locally](#quickstart)**

## Contents

- [Coderr Backend](#coderr-backend)
  - [Contents](#contents)
  - [Features and stack](#features-and-stack)
  - [Requirements](#requirements)
  - [Quickstart](#quickstart)
    - [Windows CMD](#windows-cmd)
    - [macOS](#macos)
    - [Linux](#linux)
    - [Start the API](#start-the-api)
  - [Frontend and demo](#frontend-and-demo)
  - [API endpoints](#api-endpoints)
  - [Quality assurance](#quality-assurance)
  - [Project documentation](#project-documentation)
  - [Troubleshooting](#troubleshooting)
  - [Scope](#scope)

## Features and stack

| Area | Features |
| --- | --- |
| Accounts | Registration, token login, customer and business profiles, profile editing and image uploads |
| Offers | Three package tiers per offer, search, filters, sorting and pagination |
| Orders | Package booking, purchase terms stored at checkout, order lists for participants, status updates by the provider and deletion by staff |
| Reviews | One review per customer and provider pair, rating and text updates by the author, filtering and sorting |
| Statistics | Order counts per provider and public totals for offers, business profiles and reviews, including the average rating |

The backend uses Python 3.14, Django 6.1.2, Django REST Framework 3.18.3 and SQLite. Pillow handles images, `django-cors-headers` configures browser access from the frontend, and `python-dotenv` loads local settings.

## Requirements

- Git
- Python 3.14 with `pip` and `venv`

The Python dependencies and their versions are listed in [requirements.txt](requirements.txt). The local setup uses SQLite without a separate database server. Postman Desktop is used for the optional HTTP test collections.

## Quickstart

Clone the repository and open the project directory.

```shell
git clone https://github.com/CZX93-BW/coderr-backend.git
cd coderr-backend
```

Follow the section for your operating system. Then continue with [Start the API](#start-the-api). The documented clean installation was verified on Windows using CMD.

### Windows CMD

Check that `python` reports version 3.14, then create and activate the virtual environment.

```cmd
python --version
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env
```

### macOS

Open Terminal in the project directory. These commands assume Python 3.14 is available as `python3.14`.

```sh
python3.14 --version
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

### Linux

Open a Bash shell in the project directory. These commands assume `python3.14` and its `venv` module are installed.

```sh
python3.14 --version
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
test -f .env || cp .env.example .env
```

### Start the API

With the virtual environment active, generate a secret key for your local installation.

```shell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Open `.env` next to `manage.py`. Replace the placeholder in `DJANGO_SECRET_KEY` with the generated key and keep the surrounding single quotes. The other settings in [.env.example](.env.example) are prepared for local development.

| Setting | Local configuration |
| --- | --- |
| `DJANGO_SECRET_KEY` | The generated secret key |
| `DJANGO_DEBUG` | `True` for local development and serving uploaded media |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated backend hostnames, such as `localhost,127.0.0.1` |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Frontend origins including scheme and port. The example includes `http://127.0.0.1:5500` and `http://127.0.0.1:5501`. |

Apply the migrations, run Django’s system check and start the development server.

```shell
python manage.py migrate
python manage.py check
python manage.py runserver
```

Open the [platform statistics endpoint](http://127.0.0.1:8000/api/base-info/). A fresh database returns HTTP 200 with the following values:

```json
{
  "review_count": 0,
  "average_rating": 0.0,
  "business_profile_count": 0,
  "offer_count": 0
}
```

For later sessions, activate the existing virtual environment and run `python manage.py runserver`. Run `python manage.py migrate` again after pulling new migrations.

## Frontend and demo

Start the [Coderr frontend](https://github.com/Developer-Akademie-Backendkurs/project.Coderr) separately on an origin listed in `DJANGO_CORS_ALLOWED_ORIGINS`.

With the backend running, open a second terminal in the backend directory, activate the same virtual environment and prepare the demo data.

```shell
python manage.py seed_demo
```

The command prepares the two guest accounts and a bookable offer. In the [demo walkthrough](docs/DEMO_FLOW.md), the customer books the Standard package, the provider marks the order as completed, and the customer submits a review.

To inspect records or prepare the staff-only order deletion test, create a local administrator and sign in to [Django admin](http://127.0.0.1:8000/admin/).

```shell
python manage.py createsuperuser
```

## API endpoints

The local API base URL is `http://127.0.0.1:8000/api/`. All paths in the table are relative to this URL.

Registration and login return an account token. Send it in the `Authorization` header for protected requests:

```http
Authorization: Token <token>
```

| Resource | Methods | Purpose |
| --- | --- | --- |
| `registration/` | POST | Register a customer or business account |
| `login/` | POST | Authenticate an account and retrieve its token |
| `profile/{user_id}/` | GET, PATCH | Read a profile or edit your own |
| `profiles/customer/`, `profiles/business/` | GET | List profiles by role |
| `offers/` | GET, POST | Browse offers or publish one as a provider |
| `offers/{id}/` | GET, PATCH, DELETE | Read an offer or manage one you own |
| `offerdetails/{id}/` | GET | Read the terms of one bookable package |
| `orders/` | GET, POST | List orders you participate in or book a package as a customer |
| `orders/{id}/` | PATCH, DELETE | Update the status as the provider assigned to the order or delete it as staff |
| `order-count/{business_user_id}/` | GET | Count a provider’s orders with status `in_progress` |
| `completed-order-count/{business_user_id}/` | GET | Count a provider’s orders with status `completed` |
| `reviews/` | GET, POST | Browse reviews or review a provider as a customer |
| `reviews/{id}/` | PATCH, DELETE | Edit or delete a review you wrote |
| `base-info/` | GET | Read public marketplace totals and the average rating |

The [permissions guide](docs/AUTH_AND_PERMISSIONS.md) lists the required role and ownership rules for each operation.

## Quality assurance

The clean Windows installation passed all 181 Django tests. All 16 Postman collections were reported successful, including two login cases prepared manually in Django admin. The [test report](docs/TESTING.md) records the full run and the targeted checks performed after the tests were reorganized.

Run the full Django suite from the project directory with the virtual environment active. Django creates a separate test database.

```shell
python manage.py test
```

To run the offer update and deletion tests or check for model changes that still need a migration:

```shell
python manage.py test offers_app.tests.test_update_delete
python manage.py makemigrations --check --dry-run
```

Postman runs against the local development database. The [Postman guide](postman/docs/README.md) lists the collection order, matching environments, image fixtures and account setup.

## Project documentation

| Document | What it covers |
| --- | --- |
| [Architecture](docs/ARCHITECTURE.md) | The five Django apps and the path of a booking request from routing to storage |
| [Data model](docs/DATA_MODEL.md) | Model relationships, field ownership and deletion rules |
| [Authentication and permissions](docs/AUTH_AND_PERMISSIONS.md) | Token authentication, account roles, ownership and staff access |
| [Design decisions](docs/DESIGN_DECISIONS.md) | Stable package IDs, stored booking terms and frontend URL conventions |
| [Test plan](docs/TEST_PLAN.md) | Planned checks for the 23 API operations and their boundary cases |
| [Test report](docs/TESTING.md) | Recorded Django and Postman results and commands for repeating checks |
| [Postman guide](postman/docs/README.md) | Collections, environments, local inputs and manual login checks |
| [Demo walkthrough](docs/DEMO_FLOW.md) | A booking and review from the customer’s and provider’s perspectives |
| [Development process](docs/DEVELOPMENT_PROCESS.md) | Project decisions, implementation stages, frontend integration and final checks |

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Django reports a missing secret key | Check that `.env` is next to `manage.py` and that `DJANGO_SECRET_KEY` contains your generated key. |
| The browser blocks a frontend request | Compare the browser’s origin with `DJANGO_CORS_ALLOWED_ORIGINS`, including the scheme and port. `localhost` and `127.0.0.1` are distinct origins. Restart Django after editing `.env`. |
| A protected request returns 401 | Send the token in the `Authorization` header with the `Token` prefix. If the token was deleted, log in again. |
| A write request returns 403 | Check the account role and the owner of the record. Changing an order’s status requires its assigned provider. Deleting an order requires staff access. |
| Postman cannot find an image | Set its working directory to the repository root and select the file listed in the [Postman guide](postman/docs/README.md). |

## Scope

This repository contains the local backend for the supplied Coderr frontend. Django stores application records in SQLite and uploaded files under `media/`. The recorded verification covers local installation, Django tests, HTTP checks and the frontend demo. Production hosting and the private assessment suite are outside its scope.