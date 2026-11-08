# Architecture

The backend is one Django project with five domain apps. The browser and Postman use the same HTTP interface. Django routes requests through core/urls.py to each app's api/urls.py under the common /api/ prefix.

| Module | Responsibility |
| --- | --- |
| core | Loads environment settings, installs middleware, mounts app URLs, admin and local debug media. |
| accounts_app | Extends Django users with marketplace profiles and supplies registration, token login and profile APIs. |
| offers_app | Owns offers and package tiers, validates nested input and provides filtered, paginated discovery. |
| orders_app | Resolves the purchased tier, stores an order snapshot and controls participant access. |
| reviews_app | Associates a customer's rating with a provider and limits writes by authorship. |
| base_info_app | Reads aggregates from other apps and exposes the local demo management command. |

## Trace one purchase

1. The authenticated customer sends POST /api/orders/ with an offer_detail_id.
2. The order view applies token authentication and the customer-role permission. The request determines the buyer's account.
3. The create serializer validates the ID and resolves the tier together with its offer and provider. The service receives that package and the customer.
4. The service copies the agreed fields into a new Order, including a copy of the feature list. The output serializer returns the stored terms and status.
5. A later list request builds a queryset containing rows where the requester is the customer or provider. A status update resolves one order and checks its provider before writing.

The implementation can be followed in [order views](../orders_app/api/views.py), [serializers](../orders_app/api/serializers.py) and the [booking service](../orders_app/services.py).

## Where a change belongs

Model constraints protect invariants across database writes, such as one package per offer and tier. Serializers validate client input and define response fields. Views select the action, queryset and serializer. Permission classes answer whether this caller may perform the action on this record. Services group work that crosses records or copies data between domains.

For example, changing which values a review accepts belongs in review validation. Changing who may edit an existing review belongs in the author permission. Updating the public average is an aggregation concern in base_info_app. The [design decisions](DESIGN_DECISIONS.md) explain the boundaries where these responsibilities meet.
