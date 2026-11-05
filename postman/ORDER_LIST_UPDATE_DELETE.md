# Coderr order list, update and deletion checks

Scope: C21 / E13, E15, E16, with snapshot readback for C20.
Backend baseline: commit 2d0e174; 127 Django tests reported passing.

## Local setup

1. Extract this ZIP into the backend project root. The three files go under postman/.
2. Activate the backend virtual environment and run `python manage.py runserver`.
3. Import Coderr_Order_LIST_UPDATE_DELETE.postman_collection.json into Postman Desktop.
4. Import Coderr_Order_Manage_Local.postman_environment.json.
5. Select the environment **Coderr Order Manage Local**.
6. Keep base_url as `http://127.0.0.1:8000/api` (no trailing slash).
7. Set staff_username and staff_password in your local Postman environment.
   Use an existing active Django user with is_staff=True. Your local Django
   admin account is suitable. Use its username, not its email address.
   Keep the values local/unshared. Do not paste credentials into chat.
8. Run **Coderr Order LIST UPDATE DELETE** in its original order, with one
   iteration and all 72 requests selected. No input file or image is needed.

Expected result: 206 passed assertions, zero failed assertions or execution errors.
The shipped environment file contains blank credential values. Commit that
file, not an export with populated credentials or tokens. Runtime tokens are
stored in collection variables; do not commit exports containing their values.

## Fixture relationships

The first request logs into your existing staff account. Its current participant
list is captured and must remain unchanged during this run. The collection then
registers five fresh users: customers ca, cb and empty; providers ba and bb.

| Order | Customer | Provider | Package |
| --- | --- | --- | --- |
| a | ca | ba | standard, 149.90, 3 days, -1 revisions |
| b | ca | bb | basic, 0 price, 0 days, 0 revisions |
| c | cb | bb | premium, 299.95, 7 days, 5 revisions |

Your staff account is unrelated to all three orders. It must not see them in
its list or update their statuses, but it must be able to delete them.
Run without parallel test runs or manual edits to these records.

## Coverage

- Customer and provider lists contain exactly their own purchases or sales.
- Empty user receives a bare empty array; Staff does not receive a global list.
- Participant IDs in query parameters cannot expose foreign orders;
  page_size does not enable pagination on this endpoint.
- Lists have exact response fields, numeric prices, valid timestamps and
  persisted values matching the expected state.
- Missing and invalid tokens are rejected for GET, PATCH and DELETE.
- Associated provider can set completed, cancelled and in_progress, with
  commercial data, owners, IDs and creation timestamp preserved.
- Customer, foreign customer, foreign provider and unrelated Staff cannot
  update the status. No undocumented transition restrictions are assumed.
- Invalid/missing status and extra fields return 400. Subsequent list reads
  confirm unchanged values and timestamps.
- Non-Staff participants and strangers cannot delete orders.
- Changing the original package or deleting its offer preserves previously
  booked data, verified through customer and provider list reads.
- Detail GET and PUT return 405; only the documented PATCH/DELETE are exposed.
- Staff deletion returns 204 with an empty body and removes exactly its target.
- Other orders survive deletion. PATCH and repeated DELETE of the deleted
  fixture return 404, using a known deleted ID rather than an arbitrary ID.
- After cleanup, all fixture participant lists are empty and the existing
  staff list still matches its initial state.

## Side effects and failure diagnosis

Each successful run leaves five fresh test users. It deletes its three orders
and two offers. It does not delete your Staff account or any pre-existing order
or offer. A failed/interrupted run may leave some of its own fixtures behind.
Do not use this collection against a production database.

A missing/failed staff login stops the run before fixture creation. A normal
non-Staff account can log in, but will fail the staff-deletion tests with 403.
The account must therefore have the Staff flag before running the collection.

For a failure, inspect the first failing request in the Runner's List view and
copy its recorded HTTP status, response JSON and assertion error. Do not resend
individual requests after cleanup: their records may already be deleted.

## Generator validation

All 72 scripts and 206 assertions were executed against controlled responses.
Ten deliberately faulty response/state variants were detected, including data
disclosure, global Staff listing, incorrect price types, extra fields, changed
commercial data, timestamp mutation on rejected requests, forbidden writes,
live package data instead of snapshots, missing deletion and nonempty DELETE.
Failed-login stopping and JSON serialization of quoted passwords were checked.
These checks are not a live API run. Record the actual Postman outcome separately.
