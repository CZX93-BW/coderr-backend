# Profile GET checks

1. Start Django with python manage.py runserver.
2. Run the existing Coderr Backend main collection with Coderr Local selected.
   All requests must pass. This creates fresh customer and business accounts.
3. Import Coderr_Profile_GET.postman_collection.json as a separate collection.
4. Run all seven requests once with the same Coderr Local environment.

Expected: 33 passing assertions. Existing collections and environment stay intact.
This collection only sends GET requests and never modifies accounts.
Do not edit the newly prepared profiles before this run: blank text and null
image assertions intentionally verify registration defaults.

Coverage: own and foreign profiles for both roles; exact response fields;
account identity; empty initial texts; null initial image; timestamp syntax;
missing/invalid token; nonexistent user ID 0 returning 404.

Django tests additionally verify inactive users, exact date_joined mapping,
populated text values, a user without a profile, and unequal user/profile IDs.
These cases require controlled database fixtures and are not simulated by this
collection. Image upload and PATCH are outside this collection's scope.
Timestamp syntax does not prove equality to the database value.

Keep runtime tokens out of committed environment exports.
