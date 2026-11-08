# Design decisions

## Keep package identity stable during edits

Each offer owns one basic, standard and premium tier. A partial update finds the existing tier by offer and offer_type, then changes the supplied fields on that row. Its primary key survives. Updating the offer and its tiers inside one transaction prevents the offer title from being committed if a later package write fails. See the [offer service](../offers_app/services.py).

## Preserve what the customer bought

A provider can change an advertised price or remove an offer after it has been booked. The order therefore carries its own price, delivery time, revisions, feature list, tier and title. The customer and provider remain linked to real accounts. The API only accepts a status change on order updates, and explicitly rejects extra input fields. See [order serializers](../orders_app/api/serializers.py).

## Match the supplied frontend's link contract

The offer list emits relative package paths of the form /offerdetails/12/. In an individual offer response, the package link is an absolute URL including /api/offerdetails/12/. The resulting package detail request requires authentication. Separate serializers preserve the two representations. See [offer serializers](../offers_app/api/serializers.py).

## Keep identity and role checks on the server

Registration creates the user, role profile and token in one transaction. A provider's offer author, an order's buyer and a review's author are taken from the authenticated request. Model relationships identify the owner for subsequent writes. The provider role alone cannot authorize a change to another provider's order.

## Make aggregate and list results predictable

The offer list defaults to six entries per page, with a page_size maximum of 100. It supports creator_id, min_price, max_delivery_time, search and ordering by min_price or updated_at in either direction. Price and delivery filters use the cheapest tier price and shortest tier delivery time for the offer. Explicit ordering uses an ID tie-breaker.

Reviews can be filtered by business_user_id and reviewer_id and sorted by rating or updated_at. A database constraint covers the author-provider pair. Repeating a review for that pair produces a validation error. The public summary rounds the overall average to one decimal place and returns 0.0 before the first review.

## Reuse demo accounts carefully

Repeated local demonstrations need stable guest accounts and an offer with three tiers. The seed command checks existing credentials, role and privilege flags before reusing a matching username. It stops on a conflict. This avoids silently changing an unrelated account to make a demo pass. See the [seed command](../base_info_app/management/commands/seed_demo.py).
