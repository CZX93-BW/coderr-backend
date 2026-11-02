# Profile PATCH checks

## Setup
Copy this package's postman contents into the repository's postman directory.
Keep the existing collections and environment.
Start the local backend: python manage.py runserver.
Import Coderr_Profile_PATCH.postman_collection.json into Postman Desktop.
Select Coderr Local. base_url must be http://127.0.0.1:8000/api.

This collection creates its own fresh customer and business accounts.
It does not depend on the main collection and does not overwrite its account
variables. Each full run creates two new local test users and uploaded files.
Do not export populated collection variables (they contain runtime tokens).

## Select the four upload files
Open each request below, go to Body > form-data, select the local file for
the file row and save the request:
- UPLOAD-01: postman/fixtures/profile-blue.png
- UPLOAD-02: postman/fixtures/profile-red.png
- UPLOAD-03: postman/fixtures/invalid-image.png
- UPLOAD-04: postman/fixtures/profile-blue.png

Relative paths are included. If Postman cannot resolve them, select the files
manually as above. Use the local Desktop runner, not a cloud or scheduled run.
Do not manually add Content-Type to multipart requests; Postman supplies it
with the boundary.

## Run
Run the entire collection once in its saved order, with one iteration.
Expected: 32 requests, 83 passing assertions.
Stop and investigate preparation errors; later failures may be consequences.
Each successful customer operation stores a snapshot. Verification GETs compare
the actual saved response against that snapshot. Rejected changes must preserve
it. Run all requests again to prepare fresh accounts rather than selectively
rerunning state-dependent steps.

## Coverage and limits
Covers customer text/user changes, business owner update, clearing a text field,
invalid email, null location, maximum location length, missing/invalid token,
foreign writes, missing profile, protected fields, initial upload, replacement,
invalid replacement, foreign upload, and text changes preserving the image.
The exact public response fields are checked on successful customer PATCHes.
Database-only staff/superuser flags and transaction rollback are covered by Django
tests; a public API response cannot prove their database values.
uploaded_at is not part of this endpoint's response. This collection therefore
does NOT claim to verify its persistence or update time; Django tests cover it.
Image URLs are checked as values; actual media serving must still be verified
in the frontend. Old-file cleanup and image removal are not covered.
The existing Profile GET collection expects freshly registered blank profiles.
Run it with its own main-collection preparation, not these modified accounts.

## Commit hygiene
Commit the provided JSON template, this guide and fixture files.
Do not replace the template with a Postman export containing runtime tokens or
machine-specific absolute upload paths.
