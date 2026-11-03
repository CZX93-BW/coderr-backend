# Offer creation HTTP tests (C16 / E08)

## Run

1. Start Django with `python manage.py runserver`.
2. Import the collection and the supplied `Coderr Offer Create Local` environment.
3. Select that environment. `base_url` is `http://127.0.0.1:8000/api` without a trailing slash.
4. Run the complete collection once, in its saved order, with one iteration.
5. Expected: 30 requests and 102 passing assertions.

Alternatively, use the existing Coderr Local environment if its base_url has that same value.
No upload files or manually entered IDs/tokens are needed.

## Scope

- Fresh customer and business registrations provide collection-scoped tokens and IDs.
- Business creation returns exact offer/package fields, matching values and valid IDs.
- Numeric JSON and numeric strings are accepted; price/day zero and revisions -1/0/100 are covered.
- Omitted image and explicit null both produce image=null.
- Customer, missing-token and invalid-token requests are rejected.
- Empty, incomplete, duplicate, unknown and excessive package sets are rejected.
- Required offer/package fields and invalid numeric boundaries are covered.
- A final valid request confirms subsequent creation still works.

The suite sends no requests to offer-list/detail endpoints, which are not implemented yet.
Database non-mutation after rejection, authenticated ownership and a failure after the first
package save are checked by the Django tests. HTTP status checks alone do not prove rollback.
Image uploads, feature-element strictness, inactive users and later CRUD operations are outside this suite.

## Test data and source control

Each complete successful run creates two accounts and four offers in the local development database.
They are not written to the isolated Django test database and are not deleted automatically.
Generated collection variables use the oc_ prefix, separate from the earlier suites.
The password in registration requests is public local test data; never reuse it for a real account.
Keep the supplied templates in Git. Do not commit exports containing runtime tokens.

## Commit after a successful local run

```cmd
git add postman/Coderr_Offer_CREATE.postman_collection.json postman/Coderr_Offer_CREATE_Local.postman_environment.json postman/OFFER_CREATE.md
git diff --cached --check
git diff --cached --stat
git commit -m "test(offers): add Postman coverage for offer creation"
git status --short
```
