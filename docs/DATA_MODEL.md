# Data model

Django's user owns credentials and account identity. UserProfile stores marketplace-specific fields. Offers and orders each represent package terms at a different point in time.

| Record | Fields and relationships | Persistence rule |
| --- | --- | --- |
| UserProfile | One-to-one user, type, file, uploaded_at, location, tel, description, working_hours | One profile per user. Deleting the user cascades to the profile. |
| Offer | Provider user, title, description, image and timestamps | Deleting the provider cascades to owned offers, subject to any protected references to the user. |
| OfferDetail | Parent offer, tier, title, revisions, delivery days, price, features | Unique pair of offer and tier. Deleting the offer cascades to its packages. |
| Order | Customer and provider users, copied title, price, revisions, delivery days, features, tier, status and timestamps | Both participant references use PROTECT. Booked terms survive changes to or deletion of the source offer. |
| Review | Reviewer, business user, rating, description and timestamps | Unique pair of reviewer and business user. Both user references use CASCADE. |

## Identity and field ownership

The profile detail URL uses the user ID. Username, email, first and last name live on the user. The profile serializer combines those fields with marketplace data and uses the user's join date for created_at. The profile image field stores a media reference and uploaded_at starts empty. A successful image update records an upload timestamp.

## Package and order values

An offer is created with basic, standard and premium tiers. Price has two decimal places and can be zero. Delivery time accepts zero. A revision count of -1 represents unlimited revisions, while zero means no revisions. The database uniqueness constraint prevents duplicate tier names within an offer. The API separately validates the complete set on creation.

An order starts in_progress and can store completed or cancelled. There is no foreign key from an order to its source tier. The customer and provider links remain available even if the provider later removes the offer. The [order service](../orders_app/services.py) captures the fields used to build the snapshot.

## Ratings and totals

The API accepts whole-number ratings from 1 to 5. A review refers to the provider's account, so its uniqueness applies across that provider's offers. Public totals are computed from the current offer, review and business profile tables. An empty review table gives an average of 0.0.
