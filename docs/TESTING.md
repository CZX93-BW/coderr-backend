# Testing

## Recorded results

| Check | Observed result | Scope |
| --- | --- | --- |
| Windows clean checkout, 8 November 2026 | Migrations succeeded, system check reported zero issues, 181 tests passed in 12.899 s. GET /api/base-info/ returned 200. | Local installation following the README at the pre-cleanup baseline, recorded in 15a4902. |
| HTTP verification | All 16 Postman collections reported successful. The setup, registration and login collection reported 153 passed assertions. | Local development server. Includes profile uploads, offer writes, order permissions, reviews, statistics and two manual login cases. |
| Test reorganization | Django discovered 181 tests with zero loader errors. | 22 modules across five app-level test packages at 53219f8. Discovery checks imports and count. |
| Python cleanup | pycodestyle and git diff --check produced no findings in the checked scope. Django's system check passed after sorting imports. | Generated migrations and the virtual environment were excluded from the style check. |
| Ownership regression | One targeted test passed in 0.016 s after extracting test helpers. | Offer owner and package ID protection at aafee02. |
| Final Windows check, 8 November 2026 | All 181 Django tests passed in 12.511 s. The system check passed, no migrations were pending generation, and pycodestyle reported no findings. | Full suite after test reorganization and Python documentation updates. |

The full Django result above belongs to the clean-clone checkpoint. The later discovery and focused test have narrower scopes. A passing count measures executed tests. No line-coverage percentage or result from the private assessor suite was measured here.

## Django test layers

| App | Tests discovered after the split | Representative behavior |
| --- | ---: | --- |
| accounts_app | 57 | Registration rollback, privilege restrictions, token reuse, profile ownership and image handling |
| offers_app | 45 | Package constraints, filters, pagination, atomic updates and stable IDs |
| orders_app | 32 | Snapshots, participant visibility, provider-only status and staff deletion |
| reviews_app | 41 | Rating bounds, uniqueness, author-only writes, filters and ordering |
| base_info_app | 6 | Empty and populated totals, guest login and repeatable seeding |

Run these commands from the repository root with the environment activated. Django creates a separate test database.

```shell
python manage.py test
python manage.py test orders_app.tests.test_create
python manage.py test offers_app.tests.test_update_delete.OfferUpdateDeleteAPITests.test_client_cannot_change_offer_owner_or_package_id
```

The ownership case sends one PATCH that attempts to redirect an offer and replace a package ID. It verifies the permitted title and price edits, reloads the original records and checks that the foreign offer's packages match their earlier snapshot.

## HTTP and frontend verification

Postman sends real HTTP requests and materializes data in the local development database. Import the [collections](../postman/collections/) and [environments](../postman/environments/). Start with Coderr Backend and Coderr Local, then reuse that environment for Profile GET. Follow the [collection matrix](../postman/docs/README.md) for the remaining environments, image fixtures, staff account and manual login steps. Tests expecting 400, 401, 403 or 404 pass when the corresponding error behavior is correct.

The [frontend walkthrough](DEMO_FLOW.md) records the completed browser journey. It complements the database, serializer and permission checks by showing a customer's booking from both participants' perspectives. The [original test plan](TEST_PLAN.md) preserves the planning assumptions and case design.
