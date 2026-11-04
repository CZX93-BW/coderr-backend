# Coderr order creation checks

Scope: C20 / E14, POST /api/orders/. Prepared for backend commit aa8e08c.

## Setup and execution

1. Extract the ZIP into the backend project root. It adds three files under postman/.
2. Activate the virtual environment and start Django: `python manage.py runserver`.
3. Import Coderr_Order_CREATE.postman_collection.json into Postman Desktop.
4. Import Coderr_Order_CREATE_Local.postman_environment.json.
5. Select the environment **Coderr Order Create Local**.
6. Confirm base_url is `http://127.0.0.1:8000/api` with no trailing slash.
7. Run the entire **Coderr Order CREATE** collection in its original order,
   with one iteration and all 30 requests selected. No data file is needed.

Expected result: 100 passed assertions, zero failed assertions or execution errors.
The collection needs no local images or working-directory configuration.
Run it against your local development database only.

## Coverage

- Fresh business and two customer registrations for each run.
- Three offer packages with distinct commercial data, including zero price,
  zero delivery days, zero revisions, and unlimited revisions (-1).
- Customer purchases of every package; a different customer purchasing the
  same package; repeated purchases with distinct order IDs.
- Integer package IDs and a numeric-string package ID.
- Exact 12-field order response, numeric price, participant IDs, initial
  in_progress status, valid timestamps, and all six copied package fields.
- Client-supplied owner IDs, commercial data, status, timestamps, and order ID
  cannot override server-controlled order data.
- Missing, null, blank, nonnumeric, zero, negative, fractional, boolean,
  array, and object package IDs produce 400.
- Unknown or deleted package IDs produce 404.
- Business purchase produces 403; missing or invalid token produces 401.
- A valid purchase still works after rejected requests.
- After the provider changes a package, a new order uses its new values.
- The provider can delete this run's offer after purchases; its deleted
  package can no longer be purchased.

## Limits and persistent test data

This collection does not call GET /api/orders/: that route is not implemented
at this stage. It therefore does not independently re-read old orders or
count database rows after rejected POSTs. Persistent snapshots after package
changes/deletion and absence of orders after invalid requests are covered by
the existing Django tests. Add HTTP readback checks when C21 is implemented.

Each successful run leaves three test users and nine orders. The created
offer is deleted at the end. PROTECT intentionally prevents deleting users
with orders; do not treat that as a cleanup defect. Existing unrelated data
is not modified. Never run individual dependent requests after the full run:
their package IDs refer to the deleted fixture. Start a fresh full run instead.

The unknown-ID test uses 2147483647, assumed absent in the local database.
Change it to a confirmed absent positive ID if your database contains it.
All requests explicitly disable inherited authentication and set token
headers only where required. Fresh runtime tokens are collection variables;
do not commit exports containing their populated values. The shipped files
contain no real credentials. The hardcoded password is for disposable local
test accounts only.

## Validation record

Generation check: all 30 request scripts executed with 100 passing assertions
against controlled responses. Seven deliberately faulty response variants
were detected (price type, customer, package values, status, duplicate ID,
extra response field, and acceptance of invalid requests).
This is not a live API result. Record the actual Postman run separately.

For a failure, inspect the response from that runner execution and report
the first failing request, HTTP status, JSON body, and assertion message.
Avoid resending a request after cleanup, which would create a misleading 404.
