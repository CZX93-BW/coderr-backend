# Test Plan

## Purpose and current status

Tests are derived from the Coderr API specification and the documented
clarifications provided by the instructor.

This document describes planned coverage, not completed verification.

Current verified baseline:
- Five profile model tests pass.
- Registration and the remaining business API endpoints are not implemented.
- Postman collection and environment files are not yet available.

Passing our own tests does not guarantee that all private assessment tests
will pass.

## Development workflow

1. Define the expected behavior from the API contract.
2. Write and run a focused test before implementing new behavior.
3. Confirm that it fails for the expected reason.
4. Implement the minimum required behavior.
5. Run the relevant tests.
6. Refactor while keeping tests passing.
7. Add corresponding HTTP checks to the Postman collection.
8. Record results and commit the completed change.

For new data structures, start with model tests and the required models
and migrations. Then implement the API through API tests.

Additional regression tests for existing behavior may pass immediately.
Do not introduce artificial failures to claim a red phase.

## Test layers

| Layer | Responsibility |
| --- | --- |
| Model tests | Defaults, relationships, uniqueness and deletion rules |
| API tests | Validation, authentication, permissions, responses and side effects |
| Postman | Real HTTP requests and connected workflows against the local server |
| Frontend checks | Integration with the supplied frontend, including uploads |

Model and API tests initially live in each app's `tests.py`.
Use separate test classes for their responsibilities.

Django tests use an isolated test database.
Postman uses the local development database and dedicated test accounts.

## Test identities

| Identity | Purpose |
| --- | --- |
| customer_a | Customer creating the tested order or review |
| customer_b | Another customer for ownership checks |
| business_a | Provider associated with the tested offer or order |
| business_b | Another provider for ownership checks |
| staff_user | Account for explicitly permitted staff operations |

Also test requests without a token and with an invalid token.

Do not assume that staff status bypasses ownership restrictions.
Only grant staff-specific access where the contract requires it.

## Planned Postman variables

- base_url
- run_id
- customer_a_token
- customer_a_id
- customer_b_token
- customer_b_id
- business_a_token
- business_a_id
- business_b_token
- business_b_id
- staff_token
- staff_id

The local base URL is:

http://127.0.0.1:8000/api

Use `run_id` to generate distinct account names for each run.
Capture tokens and object IDs from API responses.

Additional offer, package, order and review ID variables will be added
with their respective test workflows.

Do not commit real tokens, administrator passwords or personal data.
Destructive requests must target dedicated local test data only.

## Endpoint test matrix

| ID | Operation | Planned test groups |
| --- | --- | --- |
| E01 | POST /api/registration/ | Customer and business registration; required fields; password mismatch; invalid role; duplicate username; no partial registration |
| E02 | POST /api/login/ | Valid credentials; incorrect password; unknown user; missing fields; correct response and usable token |
| E03 | GET /api/profile/{pk}/ | Own and other profiles; unknown user ID; empty optional text fields; no password data |
| E04 | PATCH /api/profile/{pk}/ | Owner-only updates; partial updates preserve omitted fields; image upload and replacement; protected fields cannot escalate privileges |
| E05 | GET /api/profiles/business/ | Business users only; correct response fields; empty list |
| E06 | GET /api/profiles/customer/ | Customers only; exact agreed response fields; null upload timestamp without an image |
| E07 | GET /api/offers/ | Public access; filters; search; sorting; pagination; derived minimum values; relative package URLs; empty results |
| E08 | POST /api/offers/ | Business role; three valid packages; invalid or incomplete packages; atomic creation |
| E09 | GET /api/offers/{id}/ | Existing and unknown offers; response content; absolute package URLs |
| E10 | PATCH /api/offers/{id}/ | Owner versus another business user; partial package updates; image-only updates; stable package IDs; unchanged data after rejection |
| E11 | DELETE /api/offers/{id}/ | Owner versus another business user; unknown ID; 204 with an empty body |
| E12 | GET /api/offerdetails/{id}/ | Existing and unknown package IDs; correct package data |
| E13 | GET /api/orders/ | Orders involving the requesting customer or provider; unrelated orders excluded; empty list |
| E14 | POST /api/orders/ | Customer role; valid and unknown packages; copied package data remains independent of later offer changes |
| E15 | PATCH /api/orders/{id}/ | Associated provider only; other provider and customer rejected; invalid status; prohibited fields |
| E16 | DELETE /api/orders/{id}/ | Staff allowed; ordinary users rejected; unknown ID; 204 with an empty body |
| E17 | GET /api/order-count/{business_user_id}/ | Only in_progress orders for the selected provider; unrelated orders excluded; zero count; invalid provider cases |
| E18 | GET /api/completed-order-count/{business_user_id}/ | Only completed orders for the selected provider; unrelated orders excluded; zero count; invalid provider cases |
| E19 | GET /api/reviews/ | Filtering and sorting across multiple records; empty results |
| E20 | POST /api/reviews/ | Customer role; valid provider; invalid target; duplicate review returns 400; rating boundaries |
| E21 | PATCH /api/reviews/{id}/ | Reviewer-only updates; rating and description changes; protected relationships cannot be reassigned |
| E22 | DELETE /api/reviews/{id}/ | Reviewer-only deletion; unknown ID; 204 with an empty body |
| E23 | GET /api/base-info/ | Public access; empty database; known counts and average rating; rounding to one decimal place |

Each row must be expanded into individual tests during implementation.
Consult the original specification for exact payloads, response fields
and status codes before writing assertions.

## Cross-cutting checks

- Protected endpoints reject missing and invalid authentication.
- Public endpoints work without authentication.
- Ownership tests include another user with the same role.
- Rejected writes leave existing data unchanged.
- Failed multi-object writes do not leave partial records.
- Responses contain the expected fields, types and values.
- Passwords and password hashes never appear in API responses.
- Unknown resource IDs and unsupported methods are tested.
- Filters, sorting and pagination use enough records to reveal errors.
- Postman runs do not depend on manually copied database IDs.

## Confirmed boundary rules

- Price may be zero; negative prices are invalid.
- Delivery time must be an integer greater than or equal to zero.
- Revisions allow -1 for unlimited, or an integer greater than or equal to zero.
- Ratings allow integers from 1 to 5.
- A second review by the same reviewer for the same provider returns 400.
- Only the provider associated with an order may change its status.
- Average rating is 0.0 when no reviews exist.
- Optional profile text values are empty strings rather than null.
- Without a profile image, uploaded_at is null.
- A successful image upload sets uploaded_at.
- Text-only profile changes do not change uploaded_at.
- Replacing an image updates uploaded_at.

The decision to use null without an image was confirmed in the project
discussion. Image removal behavior must be settled before implementing
that case.

## Model decisions to verify

- Each profile belongs to exactly one user.
- A user cannot have multiple profiles.
- Deleting a user deletes their profile.
- Deleting one user does not delete another user's profile.
- Order snapshots remain independent of offer changes and deletion.
- Order user relationships use PROTECT.
- Review user relationships use CASCADE.

Test these decisions when the respective models are implemented.

## Details requiring explicit decisions

The authentication documentation does not explicitly define a minimum
password length or require unique email addresses.

Confirm and document the intended behavior before treating either as
an API requirement.

Profile field lengths chosen during implementation are technical design
decisions, not limits stated by the API specification.

Django model choices do not automatically validate every direct save.
Test API validation and database constraints according to their separate
responsibilities.

## Running Django tests

Run the complete suite:

    python manage.py test

Run the accounts tests:

    python manage.py test accounts_app --verbosity 2

Run the profile model test class:

    python manage.py test accounts_app.tests.UserProfileModelTests

A run containing zero tests is only a setup check.

## Postman delivery

Provide the full updated collection and environment as importable JSON
files whenever HTTP test coverage is added.

Document:
- Required local server and staff account setup
- Collection execution order
- Automatically captured tokens and IDs
- Repeat-run behavior
- Cleanup limited to dedicated test data

Do not report unimplemented endpoint checks as passed.

## Evidence and completion

For each completed task, record:
- Date and relevant commit
- Test command or collection run
- Number of executed tests and failures
- Expected red result where applicable
- Successful green result and refactor verification
- Remaining limitations or unresolved cases

Report Django test results and Postman results separately.
Only report coverage percentages when they were actually measured.