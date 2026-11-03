# Offer updates and deletion (E10/E11)

## Scope

Owner-only PATCH/DELETE, partial nested updates by offer_type, stable package IDs,
protected ownership, validation, persistence after rejected requests, image upload
and replacement, invalid/foreign uploads, and deletion of dependent packages.
Database rollback during an injected save failure remains covered by Django tests;
this collection does not simulate internal server failures.

## Files and setup

1. Extract this ZIP into the backend project root. Keep the postman/ directory.
2. Import the collection and environment; select **Coderr Offer Update Delete Local**.
3. Start Django with `python manage.py runserver`.
4. In Postman Settings > General, set Working directory to the backend project root:
   `C:\Users\Bastian\Desktop\coderr-backend`.
5. The four UPLOAD requests refer to files under `postman/fixtures/`.
   If Postman cannot resolve them, open each UPLOAD request, choose Body > form-data,
   reselect the corresponding local file in the image row, and save the request.
   First/foreign: offer-blue.png; replacement: offer-red.png;
   invalid replacement: offer-invalid.png. Do not set Content-Type manually.
6. Run the whole collection in its original order, one iteration.

Expected: **100 requests, 246 passing assertions**.
Folder 01: 65 requests / 157 assertions.
Folder 02: 35 requests / 89 assertions.
Folder 02 depends on accounts created by folder 01. Run it in the same collection.

## Data and repeat runs

Each complete run uses a new GUID for three usernames: owner/other business and
customer. Password is `CoderrWrite!83_TestOnly` (test accounts only).
Requests store runtime tokens and IDs in collection variables, not in exported
credentials. Before sharing a later export, remove runtime ow_* variables.

Only offers A and C created by this run are deleted. Offer B and the three accounts
remain. Uploaded files may remain after replacement/deletion: this collection
checks database records and API results, not automatic file cleanup.

missing_id defaults to 2147483647. If this ID exists locally, replace it with a
known unused positive ID in collection variables.

## Results and next step

A 400/401/403/404 is expected in its named negative request. The test assertion
must pass. ENOENT means Postman could not read a local fixture and the request was
not sent; correct the file selection before repeating the run.

After all checks pass, commit the three Postman files and three offer fixtures.
Then verify editing, image replacement and deletion of an owned disposable offer
in the supplied frontend. C19 is complete after that integration check.
