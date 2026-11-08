# Authentication and permissions

Send POST /api/registration/ with username, email, password, repeated_password and type (customer or business). Login takes username and password. Both successful responses contain token, username, email and user_id. An existing token is reused on login. If an active user's token was deleted, a successful login issues a replacement.

Protected requests use the Authorization header with the value Token followed by a space and the token. Django admin uses its own login. Staff is a Django account flag independent of the marketplace profile role.

| Operation | Allowed caller | Scope |
| --- | --- | --- |
| Register, log in, list offers, read base info | Public | Registration and login validate their input. |
| Read profiles and role lists | Authenticated user | Reading another user's profile is allowed. |
| Edit profile | Profile owner | The URL identifies the linked user. |
| Read a single offer or tier | Authenticated user | Package information is available for booking. |
| Create offer | Business account | The server assigns the author from the request. |
| Edit or delete offer | Offer owner | A different provider cannot manage it. |
| Create order | Customer account | The provider and terms come from the selected package. |
| List orders | Authenticated user | Rows where this user is the buyer or provider. |
| Update order status | Business account attached to that order | Other business accounts and the customer cannot change status. |
| Delete order | Authenticated staff user | Staff authority here is specific to deletion. |
| Read provider order counts | Authenticated user | Provider ID identifies the counter, independently of the caller. |
| List reviews | Authenticated user | Results may be filtered by provider or reviewer. |
| Create review | Customer account | Target must have a business profile. The request supplies authorship. |
| Update or delete review | Review author | Editing allows rating and description. |

## Distinguishing failures

A missing or invalid token on a protected action yields 401. A valid account lacking the required role or object ownership receives 403. A missing object can yield 404. Invalid input, duplicate reviews and rejected login credentials yield 400. A successful deletion returns 204 with an empty response.

For example, to check provider isolation, create an order for provider A and send the same status PATCH with provider B's token. Check both the 403 response and the stored status. The [Postman guide](../postman/docs/README.md) describes the accounts and per-collection preconditions for these checks.
