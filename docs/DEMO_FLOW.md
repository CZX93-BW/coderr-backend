# Local demo flow

Verified on 2026-11-06.

- `python manage.py seed_demo` prepared the guest accounts and demo offer.
- Customer guest `andrey` ordered the Standard package from `kevin`.
- Business guest `kevin` opened the same order and marked it as completed.
- `andrey` saw the updated status and submitted a review for `kevin`.
- The rating and review text were visible after reloading Kevin's profile.
- All 181 Django tests passed, including both seed tests.