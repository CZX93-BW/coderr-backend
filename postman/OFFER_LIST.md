# Offer list API checks (E07)

## Run locally

1. Start Django from the backend directory: `python manage.py runserver`.
2. Import `Coderr_Offer_LIST.postman_collection.json` and
   `Coderr_Offer_LIST_Local.postman_environment.json` into Postman.
3. Select **Coderr Offer List Local**. Its `base_url` is
   `http://127.0.0.1:8000/api` (no trailing slash).
4. Run the complete **Coderr Offer LIST** collection in its original order,
   one iteration, with every request selected. No image selection is needed.
5. Expected result: **50 requests / 150 passed assertions**.
   These counts describe the generated collection; verify them against the local run.

## Test data

Each complete run creates two fresh business accounts and seven offers with
three packages each. A random run marker isolates searches from existing data.
Tokens and generated IDs are stored in collection variables during the run.
The run does not delete existing data or remove its own fixtures.
Do not share runtime exports containing real tokens; commit the supplied templates.
No personal credentials are required. The fixture password is for local testing only.

## Coverage

- Anonymous and authenticated list access; exact response fields and saved data.
- Numeric minimum price and delivery time, including zero. The two minima come
  from different packages to catch incorrect aggregate calculations.
- Relative package links `/offerdetails/<id>/`, without `/api/`.
- Creator, minimum-price and maximum-delivery filters, equality and combinations.
- Case-insensitive title and description search; no matching results.
- Ascending/descending price and update-time ordering.
- Default six-item pagination, a real second page, custom page size and next links.
- Empty frontend filter values; field-specific 400 errors for invalid values.
- Valid requests continue to work after validation errors.

## Scope

The seven fixtures verify that page_size=101 is accepted, but cannot prove the
exact 100-item cap. No fixture with 101 offers is created.
Update-time checks allow equal timestamps. No artificial updates are required.
Empty results are checked via an unmatched search; the empty-database case is
covered separately by Django tests.
Image uploads and package-detail retrieval are outside this list collection.
Only the supplied query cases are covered; this is not exhaustive input fuzzing.
Collection syntax and assertion logic are checked before delivery. Actual API
behavior must be verified by running against the local Django server.

## Troubleshooting

- Connection refused: start Django and check the selected environment.
- 401 on preparation: run from the first registration request; do not skip PREP.
- Setup/fixture failures: inspect the first failed request and its response first.
  Later checks depend on all seven offers having been created successfully.
- After editing requests, save before starting the Collection Runner.
