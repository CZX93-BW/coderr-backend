# Development process

Coderr was a solo backend project for an existing marketplace frontend. A customer had to be able to book a package, then see the same order after the provider changed its status. This account-to-order workflow guided the implementation and the final browser check.

## 1. API requirements

The project plan grouped 23 API operations into five areas: accounts, offers, orders, reviews and platform statistics. Each Trello task identified the caller, the expected response and the records a request could change.

Several details needed clarification before implementation. A second review by the same customer for the same provider should return HTTP 400. Only the provider attached to an order should be able to change its status. Package links have two documented forms: a relative path in the offer list and an absolute URL in the offer detail response. Each case became a specific API check.

## 2. Local setup and the first model

The first commits added Git ignore rules, pinned dependencies and configured Django for the local frontend. Work on the data model started with a profile linked to a Django user. The first model test landed in `aaf40b1`. Subsequent tests checked that a user could have only one profile and that deleting a user also removed the linked profile (`f118dab`, `38937c4`).

This distinction mattered for registration. Django's user record holds the credentials. The profile holds the marketplace role. Registration creates both records and an authentication token in one transaction. A rollback test checks what happens if a write fails partway through.

The [test plan](TEST_PLAN.md) describes the intended TDD workflow. Model tests covered relationships and constraints first. Request tests then covered validation, permissions, response fields and database changes.

## 3. Feature development

| Stage | Implementation | Selected commits |
| --- | --- | --- |
| Accounts | Registration and login supplied tokens for customer and business accounts. Profile tests covered public-facing fields, authenticated reads and owner-only edits. | Registration `6f6ba51`, rollback and privileges `1caa37d`, login `23e2bb1` |
| Offers | Providers could create three package tiers. A partial update had to retain the ID of each existing tier so the frontend could still use its package links. | Models `85c2cb0`, creation `445e922`, owner-only updates `535f0db` |
| Orders | Booking copied the selected tier's terms into the order. A test changed the original package and checked that the booked price and services stayed the same. | Order model `2b9e406`, booking `aa8e08c`, order access `2d0e174` |
| Reviews and statistics | Customers could review a provider once. The public statistics endpoint used the stored reviews to calculate the average rating. | Review constraint `3bae2b2`, creation `e9aa00d`, statistics `a39dc75` |

Postman collections followed the corresponding features. For example, `445e922` added offer creation and `f81f314` added its HTTP checks. After a rejected write, the tests also inspected stored records to catch partial updates that an HTTP status check alone would miss.

## 4. Frontend integration

Profile uploads revealed a local routing issue. Django accepted the uploaded image, but the frontend also needed a working URL to display it. Commit `d7d044e` added the development route for uploaded media.

The demo command in `ccaceaa` prepared two guest accounts and a sample offer. On 6 November 2026, the customer guest booked the Standard package. The provider guest opened the order and marked it as completed. The customer saw the updated status, submitted a review and could still see it after reloading the provider's profile. The steps are recorded in the [demo walkthrough](DEMO_FLOW.md).

## 5. Installation from a clean clone

On 8 November 2026, the backend was installed from the README in a second Windows checkout with a fresh virtual environment and SQLite database. All migrations applied, Django's system check passed and all 181 tests passed in 12.899 seconds. The empty statistics endpoint returned HTTP 200.

All 16 Postman collections also passed against the local server. Two login cases required manual preparation in Django admin. Deactivating the customer exercised rejection of an inactive account. Reactivating the customer and deleting its token exercised token creation on the next successful login.

The documentation review also caught two outdated statements in the test plan. The repository already contained the implemented endpoints, 16 Postman collections and 12 environments. Commits `e9b89ef` and `15a4902` updated the plan and recorded the Django test result.

## 6. Code and test cleanup

The checklist review covered routing, permissions, model relationships, Git history and Python style. Four test files had grown to between 578 and 1,022 lines. During the split into smaller modules, two login test classes were found with the same name. Python loaded the later definition. It already checked the response fields and token count covered by the earlier class.

| Commit | Change and check |
| --- | --- |
| `53219f8` | Moved tests into 22 modules across five apps. Django discovered all 181 tests with zero loader errors. |
| `1369917` | Fixed blank lines, file endings and long lines. The initial style check had reported 90 findings. After the test split, 68 remained. The formatting pass cleared them. |
| `3973f70` | Sorted imports and removed unused Django scaffold code from seven modules. Django's system check and Git's whitespace check passed. |
| `aafee02` | Moved setup and assertions out of long test methods. The offer ownership test passed after the change. |
| `7ba6dea` | Added English docstrings to functions, methods and test cases. All 371 function and method definitions had a docstring. |

The offer ownership test still sends one PATCH request. It checks that the owner can change the offer title and package price, that the package keeps its ID and that the other provider's records match their state before the request.

## 7. Running Coderr and checking the results

Follow the [README](../README.md) to start Coderr locally. The [test record](TESTING.md) lists the results from the clean Windows installation and the checks run after the tests were reorganized. The [Postman guide](../postman/docs/README.md) gives the collection order, local test files and account setup for repeating the HTTP checks.
