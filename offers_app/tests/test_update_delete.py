from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from offers_app.models import Offer, OfferDetail


class OfferUpdateDeleteAPITests(APITestCase):
    def setUp(self):
        self.owner = self.create_user("edit_owner", "business")
        self.other = self.create_user("edit_other", "business")
        self.customer = self.create_user("edit_customer", "customer")
        self.offer = self.create_offer(self.owner, "Original offer")
        self.foreign_offer = self.create_offer(self.other, "Foreign offer")
        self.url = f"/api/offers/{self.offer.pk}/"
        self.authenticate(self.owner)
        self.configure_temporary_media()

    def create_user(self, username, account_type):
        user = get_user_model().objects.create_user(username=username)
        UserProfile.objects.create(user=user, type=account_type)
        return user

    def create_offer(self, user, title):
        offer = Offer.objects.create(
            user=user, title=title, description="Original description",
        )
        for package_type in ("basic", "standard", "premium"):
            OfferDetail.objects.create(
                offer=offer,
                title=f"{package_type} package",
                offer_type=package_type,
                revisions=2,
                delivery_time_in_days=5,
                price=Decimal("100.00"),
                features=["Responsive layout"],
            )
        return offer

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def snapshot(self):
        return (
            list(Offer.objects.order_by("pk").values()),
            list(OfferDetail.objects.order_by("pk").values()),
        )

    def send_write_request(self, method):
        if method == "patch":
            return self.client.patch(
                self.url, {"title": "Unauthorized change"}, format="json",
            )
        return self.client.delete(self.url)

    def test_owner_can_update_title_without_changing_packages(self):
        before = list(self.offer.details.order_by("pk").values())
        response = self.client.patch(
            self.url, {"title": "Updated offer"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, "Updated offer")
        self.assertEqual(self.offer.description, "Original description")
        self.assertEqual(self.offer.user_id, self.owner.pk)
        self.assertEqual(
            list(self.offer.details.order_by("pk").values()), before,
        )

    def test_owner_can_update_one_package_and_preserve_ids(self):
        before = list(self.offer.details.order_by("pk").values())
        payload = {"details": [{"offer_type": "standard", "price": "125.50"}]}
        response = self.client.patch(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for package in before:
            if package["offer_type"] == "standard":
                package["price"] = Decimal("125.50")
        self.assertEqual(
            list(self.offer.details.order_by("pk").values()), before,
        )
        self.assertEqual(len(response.data["details"]), 3)

    def test_owner_can_delete_offer_and_its_packages(self):
        package_ids = list(self.offer.details.values_list("pk", flat=True))
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Offer.objects.filter(pk=self.offer.pk).exists())
        self.assertFalse(
            OfferDetail.objects.filter(pk__in=package_ids).exists(),
        )
        self.assertTrue(
            Offer.objects.filter(pk=self.foreign_offer.pk).exists(),
        )
        self.assertEqual(self.foreign_offer.details.count(), 3)

    def test_foreign_users_cannot_update_or_delete_offer(self):
        before = self.snapshot()
        for user in (self.other, self.customer):
            self.authenticate(user)
            for method in ("patch", "delete"):
                with self.subTest(user=user.username, method=method):
                    response = self.send_write_request(method)
                    self.assertEqual(
                        response.status_code, status.HTTP_403_FORBIDDEN,
                    )
                    self.assertEqual(self.snapshot(), before)

    def test_anonymous_user_cannot_update_or_delete_offer(self):
        self.client.credentials()
        before = self.snapshot()
        for method in ("patch", "delete"):
            with self.subTest(method=method):
                response = self.send_write_request(method)
                self.assertEqual(
                    response.status_code, status.HTTP_401_UNAUTHORIZED,
                )
                self.assertEqual(self.snapshot(), before)

    def test_invalid_package_prevents_all_offer_changes(self):
        before = self.snapshot()
        payload = {
            "title": "Must not be saved",
            "details": [{"offer_type": "standard", "price": "-0.01"}],
        }
        response = self.client.patch(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.snapshot(), before)

    def configure_temporary_media(self):
        media_directory = TemporaryDirectory()
        self.addCleanup(media_directory.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_directory.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

    def create_test_image(self):
        content = BytesIO()
        Image.new("RGB", (2, 2), "blue").save(content, format="PNG")
        return SimpleUploadedFile(
            "offer.png", content.getvalue(), content_type="image/png",
        )

    def test_owner_can_upload_image_without_changing_packages(self):
        before = list(self.offer.details.order_by("pk").values())
        response = self.client.patch(
            self.url, {"image": self.create_test_image()}, format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.image.name)
        self.assertTrue(
            self.offer.image.storage.exists(self.offer.image.name),
        )
        self.assertEqual(self.offer.title, "Original offer")
        self.assertEqual(
            list(self.offer.details.order_by("pk").values()), before,
        )

    def test_invalid_image_prevents_text_changes(self):
        before = self.snapshot()
        invalid_image = SimpleUploadedFile(
            "invalid.png", b"not an image", content_type="image/png",
        )
        response = self.client.patch(
            self.url,
            {"title": "Must not be saved", "image": invalid_image},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.snapshot(), before)

    def test_invalid_package_identifiers_preserve_all_data(self):
        cases = [
            [{"price": "25.00"}],
            [{"offer_type": "unknown", "price": "25.00"}],
            [{"offer_type": "basic"}, {"offer_type": "basic"}],
        ]
        before = self.snapshot()
        for details in cases:
            with self.subTest(details=details):
                response = self.client.patch(
                    self.url, {"details": details}, format="json",
                )
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST,
                )
                self.assertEqual(self.snapshot(), before)

    def ownership_change_payload(self):
        foreign_package = self.foreign_offer.details.get(offer_type="basic")
        return {
            "user": self.other.pk,
            "title": "Allowed title",
            "details": [{
                "offer_type": "basic",
                "id": foreign_package.pk,
                "price": "35.00",
            }],
        }

    def test_client_cannot_change_offer_owner_or_package_id(self):
        package = self.offer.details.get(offer_type="basic")
        foreign_before = list(self.foreign_offer.details.order_by("pk").values())
        response = self.client.patch(
            self.url, self.ownership_change_payload(), format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        package.refresh_from_db()
        self.assertEqual(self.offer.user_id, self.owner.pk)
        self.assertEqual(self.offer.title, "Allowed title")
        self.assertEqual(package.price, Decimal("35.00"))
        self.assertEqual(self.offer.details.get(offer_type="basic").pk, package.pk)
        self.assertEqual(
            list(self.foreign_offer.details.order_by("pk").values()),
            foreign_before,
        )

    def fail_standard_package_save(self, instance, *args, **kwargs):
        if instance.offer_type == "standard":
            raise RuntimeError("Simulated package save failure")
        return self.original_package_save(instance, *args, **kwargs)

    def test_save_failure_rolls_back_offer_and_previous_package(self):
        before = self.snapshot()
        self.original_package_save = OfferDetail.save
        payload = {
            "title": "Must be rolled back",
            "details": [
                {"offer_type": "basic", "price": "25.00"},
                {"offer_type": "standard", "price": "50.00"},
            ],
        }
        with patch.object(
            OfferDetail, "save", autospec=True,
            side_effect=self.fail_standard_package_save,
        ) as save_package:
            with self.assertRaisesMessage(RuntimeError, "Simulated package"):
                self.client.patch(self.url, payload, format="json")
        self.assertEqual(save_package.call_count, 2)
        self.assertEqual(self.snapshot(), before)

    def test_unknown_offer_cannot_be_updated_or_deleted(self):
        missing_id = Offer.objects.order_by("-pk").first().pk + 1000
        self.url = f"/api/offers/{missing_id}/"
        before = self.snapshot()
        for method in ("patch", "delete"):
            with self.subTest(method=method):
                response = self.send_write_request(method)
                self.assertEqual(
                    response.status_code, status.HTTP_404_NOT_FOUND,
                )
                self.assertEqual(self.snapshot(), before)
