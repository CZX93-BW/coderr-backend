# Coderr Postman Tests

## Current scope

This initial collection contains two CORS preflight requests with ten named
tests. It does not yet cover E01-E23 or implement account creation.

- SETUP-01: approved origin, six tests.
- SETUP-02: unapproved origin, four tests.

Both requests use OPTIONS against `{{base_url}}/` and do not modify data.
The middleware can answer them before business API routes exist. A successful
preflight does not prove that a business endpoint exists or is authorized.

## Prerequisites

1. Use the Postman desktop application.
2. Start the Django development server in the backend project:

```bat
.venv\Scripts\activate.bat
python manage.py runserver
```

3. Configure `DJANGO_CORS_ALLOWED_ORIGINS=http://127.0.0.1:5500` in the local
   backend `.env`, with CORS enabled for `/api/` in Django settings.
4. Restart the server after environment changes.

Live Server does not need to run for these checks: the requests supply the
Origin header explicitly. No staff account or token is needed for this setup
folder. Staff credentials will be required only when staff API tests are added.

## Import and run

1. Import `Coderr_Backend.postman_collection.json` into Postman.
2. Import `Coderr_Local.postman_environment.json`.
3. Select the `Coderr Local` environment.
4. Open `Coderr Backend` > `00 - Setup and CORS`.
5. Send SETUP-01 and inspect the test results: expected six passes.
6. Send SETUP-02 and inspect the test results: expected four passes.
7. Run the entire collection once with one iteration: expected two requests,
   ten passed tests and zero failures.

These are expected outcomes, not a record of an executed local Postman run.

## Variables

`base_url` is `http://127.0.0.1:8000/api`, without a trailing slash.
`frontend_origin` is `http://127.0.0.1:5500`.
`unapproved_origin` is `http://127.0.0.1:5501`.

The scripts deliberately check these two origins against the agreed local
configuration. If the local frontend address changes, update the Django
configuration, environment and the corresponding assertions together.

`run_id` and the customer/business/staff ID and token variables are empty
placeholders for future API tests. They are not used or populated in this
initial version. There are no hard-coded database IDs or real credentials.

## What the assertions mean

`pm.test` defines a named test. `pm.response` reads the HTTP response.
`pm.expect` checks that actual values match the expected contract.

The approved request checks status, empty body, Vary, exact allowed origin,
allowed authorization header and allowed GET method.

The unapproved request checks status, empty body, Vary and the absence of an
Access-Control-Allow-Origin header. A 200 response is expected even when
an origin has no CORS permission; the missing header is decisive.

Postman does not enforce browser CORS. These requests verify the server's
headers. Real browser integration is a separate later check.

The response body is deliberately empty, so no JSON-body assertion is used.
JSON response checks will be added with the business endpoints.

## Repeated execution and troubleshooting

Run the two requests repeatedly without cleanup; they create no records.
A connection error usually means the local server is not running on port 8000.
Unresolved variables usually mean `Coderr Local` has not been selected.
If SETUP-01 lacks the allow-origin header, inspect the environment value,
Django CORS settings and server restart. If SETUP-02 receives an allow-origin
header, check that port 5501 is not allowed and wildcard access is disabled.

## Recording results

Record date, backend commit, Postman request/test counts and failures on C09.
Do not merge Postman counts with the five existing Django model tests.
Commit the template files only. Keep future live token/password values local;
do not overwrite the repository template with an export containing secrets.

## Sources

https://learning.postman.com/docs/tests-and-scripts/write-scripts/test-examples/
https://github.com/adamchainz/django-cors-headers
