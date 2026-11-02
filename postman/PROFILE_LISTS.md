# Profile list checks (C14)

## Run
1. Copy these two files into the backend repository's postman directory.
2. Start the backend with python manage.py runserver.
3. Import Coderr_Profile_Lists.postman_collection.json in Postman Desktop.
4. Select Coderr Local with base_url http://127.0.0.1:8000/api.
5. Run the entire collection in its saved order, one iteration.

Expected: 12 requests, 40 passing assertions. No file selection is required.
The collection creates one fresh customer and one fresh business account on each
run. It stores its own lists_* variables at collection scope and does not modify
existing customer_a/business_a environment values. Existing database records
are retained. Repeated runs create additional local test accounts.

## Coverage
- Both account types can read both lists.
- Responses are arrays, without a pagination envelope.
- Every entry has exactly the documented fields and the correct account type.
- Each prepared account appears exactly once in its matching list.
- The prepared opposite account type is excluded.
- Prepared names and business profile texts match their saved values.
- Fresh profiles have no image; the fresh customer upload timestamp is null.
- Missing and invalid tokens return 401 and a detail-only error object.

Empty lists are covered by Django tests, since this collection must not delete
existing local accounts. Non-null image URLs/timestamps and inactive tokens are
not exercised by this collection. A passing run does not imply exhaustive coverage.

## Commit
Commit the original JSON template and this guide. Do not overwrite the template
with an export containing runtime collection tokens. The template contains no
real account tokens. No frontend files are part of this change.
