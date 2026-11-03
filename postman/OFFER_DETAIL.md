# Offer and package detail API checks (C18 / E09 / E12)

## Run locally

1. Start Django: `python manage.py runserver`.
2. Import the collection and environment JSON files from this directory.
3. Select **Coderr Offer Detail Local**. The base URL must be
   `http://127.0.0.1:8000/api` without a trailing slash.
4. Run the entire **Coderr Offer DETAIL** collection in its original order,
   one iteration, with all requests selected.
5. Expected result: **22 requests / 61 passed assertions**.

## Fixtures and isolation

Every complete run creates two business accounts, one customer account and
two offers with three distinct packages each. No existing records are changed
or deleted. Test records remain in the local database after the run.
Random usernames and a unique search marker isolate repeated runs.
Tokens and IDs are stored in collection variables during execution.
Commit the supplied templates, not runtime exports containing tokens.
No personal credentials or file selection are needed.

## Coverage

- Offer retrieval by customer, owner and a different business user.
- Exactly ten offer fields, correct owner and independent price/delivery minima.
- Different offers return their own package IDs, without mixing associations.
- Absolute package URLs with `/api/`, derived from the configured base URL.
- Real requests following all three returned package URLs.
- Exactly eight package fields, all values, numeric decimal prices, zero values,
  feature lists and unlimited revisions (-1).
- Package access for the owner and another business user.
- Missing/invalid tokens return 401 on both detail endpoints.
- Unknown IDs return 404 on both endpoints.
- Public offer listing still returns relative package URLs without `/api/`.
- Read requests preserve offer fields and timestamps.

## Limits and troubleshooting

`missing_id=2147483647` is assumed absent from the local offer and package tables.
If this ID actually exists, choose an absent positive integer in the collection
variables. The collection does not delete records to manufacture a 404.
Images are omitted; offer-image upload belongs to the later update workflow.
Inactive-user tokens, write methods and other endpoints are outside this collection.
Script validation uses controlled fixtures; the actual API run is performed locally.
If PREP fails, inspect its first failed response before interpreting later failures.
For connection errors, ensure Django is running and the environment is selected.

## Frontend check after the API run

Log in with an existing test account using its username, search for `Detail fixture`,
open a test offer and inspect its package tabs and corresponding values.
Ordering, reviews and statistics have separate implementation steps.
If the page fails, inspect the failing request URL and status before changing code.
