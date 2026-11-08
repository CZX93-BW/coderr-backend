# Coderr API tests in Postman

## Run locally

1. Start the migrated backend from the repository root with `python manage.py runserver`. Use a local development database. The collections create accounts, offers, orders, reviews and media files.
2. In Postman Desktop, import the collection and environment JSON files from [collections](../collections/) and [environments](../environments/). Select the environment listed for the collection below. The supplied `base_url` is `http://127.0.0.1:8000/api`.
3. Start with **Coderr Backend** and **Coderr Local**. Set `frontend_origin` to `http://127.0.0.1:5500` and `unapproved_origin` to `https://untrusted.invalid` if reusing an imported environment. The former must be allowed in Django's CORS settings. The latter is sent as an Origin header to the local backend.
4. Choose **Run collection**, select every request, keep the saved order and use one iteration. Then run **Coderr Profile GET** with the same environment and the freshly registered profiles. **Coderr Login - Manual Preconditions** uses the individual steps below.
5. Run the other collections one at a time. Each prepares its own records. Avoid concurrent edits while a run compares lists, counts or timestamps.

## Collections

The request counts below include setup, error cases and readbacks. A successful run executes every selected request with zero failed assertions, skips or script errors. A 4xx response is expected when a request checks a rejection.

| Collection | Environment | Requests | Behaviour covered and setup |
| --- | --- | ---: | --- |
| [Coderr Backend](../collections/Coderr_Backend.postman_collection.json) | [Coderr Local](../environments/Coderr_Local.postman_environment.json) | 36 | Register customer and business accounts, check rejected registrations and login attempts, inspect CORS preflight headers. |
| [Coderr Profile GET](../collections/Coderr_Profile_GET.postman_collection.json) | [Coderr Local](../environments/Coderr_Local.postman_environment.json) | 7 | Read own and other profiles, verify registration defaults, check missing profiles and invalid tokens. Run directly after Coderr Backend. |
| [Coderr Login - Manual Preconditions](../collections/Coderr_Login_Manual.postman_collection.json) | [Coderr Local](../environments/Coderr_Local.postman_environment.json) | 2 | Check an inactive account and token reissuance. Prepare and send each request separately as described below. |
| [Coderr Profile PATCH](../collections/Coderr_Profile_PATCH.postman_collection.json) | [Coderr Local](../environments/Coderr_Local.postman_environment.json) | 32 | Edit text and images, enforce ownership and read back accepted and rejected changes. Select the four profile uploads below. |
| [Coderr Profile Lists](../collections/Coderr_Profile_Lists.postman_collection.json) | [Coderr Local](../environments/Coderr_Local.postman_environment.json) | 12 | Read both role lists as a customer and provider. Check membership, response fields and authentication. |
| [Coderr Offer CREATE](../collections/Coderr_Offer_CREATE.postman_collection.json) | [Coderr Offer Create Local](../environments/Coderr_Offer_CREATE_Local.postman_environment.json) | 30 | Create the three package tiers as a provider. Check numeric boundaries, invalid package sets and permissions. |
| [Coderr Offer LIST](../collections/Coderr_Offer_LIST.postman_collection.json) | [Coderr Offer List Local](../environments/Coderr_Offer_LIST_Local.postman_environment.json) | 50 | Check public listings, search, combined filters, pagination, sorting and price and delivery minima. |
| [Coderr Offer DETAIL](../collections/Coderr_Offer_DETAIL.postman_collection.json) | [Coderr Offer Detail Local](../environments/Coderr_Offer_DETAIL_Local.postman_environment.json) | 22 | Read offers and follow their package links. Check package values, authentication and missing IDs. |
| [Coderr Offer UPDATE DELETE](../collections/Coderr_Offer_UPDATE_DELETE.postman_collection.json) | [Coderr Offer Update Delete Local](../environments/Coderr_Offer_UPDATE_DELETE_Local.postman_environment.json) | 100 | Update individual packages, replace images and delete an offer with its packages. Check ownership and stable package IDs. Select the four offer uploads below. |
| [Coderr Order CREATE](../collections/Coderr_Order_CREATE.postman_collection.json) | [Coderr Order Create Local](../environments/Coderr_Order_CREATE_Local.postman_environment.json) | 30 | Buy a package as a customer. Verify the stored package values and rejected attempts to override order data. |
| [Coderr Order LIST UPDATE DELETE](../collections/Coderr_Order_LIST_UPDATE_DELETE.postman_collection.json) | [Coderr Order Manage Local](../environments/Coderr_Order_Manage_Local.postman_environment.json) | 72 | List participant orders, change status as the provider and delete as staff. Set both staff credentials before starting. |
| [Coderr Order COUNT](../collections/Coderr_Order_COUNT.postman_collection.json) | [Coderr Order Count Local](../environments/Coderr_Order_Count_Local.postman_environment.json) | 82 | Count in-progress and completed orders per provider. Check zero counts, status changes and excluded cancelled orders. |
| [Coderr Review CREATE](../collections/Coderr_Review_CREATE.postman_collection.json) | [Coderr Review Create Local](../environments/Coderr_Review_CREATE_Local.postman_environment.json) | 47 | Submit customer ratings from 1 to 5. Check duplicate reviews, invalid providers and token-derived authorship. |
| [Coderr Review LIST](../collections/Coderr_Review_LIST.postman_collection.json) | [Coderr Review List Local](../environments/Coderr_Review_LIST_Local.postman_environment.json) | 48 | Filter by provider and reviewer, combine filters and order by rating or update time. Check empty results and invalid queries. |
| [Coderr Review UPDATE DELETE](../collections/Coderr_Review_UPDATE_DELETE.postman_collection.json) | [Coderr Review Update Delete Local](../environments/Coderr_Review_UPDATE_DELETE_Local.postman_environment.json) | 60 | Edit and delete a review as its author. Read back rejected changes and verify that other reviews survive deletion. |
| [Coderr Base Info](../collections/Coderr_Base_Info.postman_collection.json) | [Coderr Base Info Local](../environments/Coderr_Base_Info_Local.postman_environment.json) | 36 | Compare public statistics with offer, profile and review data. Check the rounded average after review creation, update and deletion. |

## Local inputs

**Profile and offer images.** In Postman Desktop, set the working directory to the repository root, which contains `manage.py`. The requests resolve files under [postman/fixtures](../fixtures/). If a file is missing, open the request, choose **Body → form-data**, select the file under **Value**, and save. Postman sets the multipart boundary.

| Request | Profile PATCH · field `file` | Offer UPDATE DELETE · field `image` |
| --- | --- | --- |
| First image | `profile-blue.png` | `offer-blue.png` |
| Replacement image | `profile-red.png` | `offer-red.png` |
| Invalid replacement | `invalid-image.png` | `offer-invalid.png` |
| Foreign account upload | `profile-blue.png` | `offer-blue.png` |

**Staff access.** For **Coderr Order Manage Local**, set the local values of `staff_username` and `staff_password` to the credentials of an active local Django staff user. Create one with `python manage.py createsuperuser` if needed. A customer or provider account cannot perform the successful deletion check.

**Manual login checks.** Use the `customer_a_username` created by **Coderr Backend**. Sign in to the [local Django admin](http://127.0.0.1:8000/admin/) with an administrator account.

1. Deactivate the generated customer, save and send **E02-M01**. Expect HTTP 400. Reactivate the customer and save.
2. Delete only this customer's token in Django admin. Keep the old `customer_a_token` in Postman. Send **E02-M02** once. Expect HTTP 200 and a different token. Check that the customer has one token in admin.

**Platform statistics.** Keep `expect_empty_start=false` for a seeded or previously used database. The collection reads the starting totals before creating its records. Use `true` only with a freshly migrated, empty database.

## Data and repeat runs

The collections generate disposable users and capture IDs and tokens at runtime. Accounts remain after execution, and some collections retain offers, orders, reviews or uploaded files. Use the supplied environment templates for imports. Keep populated exports, tokens and staff passwords local.

For a failure, open the first failing request in the runner results and inspect its recorded status, response and assertion. Restart the complete collection after correcting its input. A successful deletion makes the original ID unsuitable for replaying earlier requests. The Django suite covers database constraints and transaction rollback separately with `python manage.py test`.
