from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile


class CustomerProfileListAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="customer_list_user",
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            type=UserProfile.AccountType.CUSTOMER,
        )
        self.token = Token.objects.create(user=self.user)
        self.url = "/api/profiles/customer/"

    def test_customer_list_without_token_is_rejected(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_customer_list_returns_documented_fields(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assert_customer_profile(response)

    def assert_customer_profile(self, response):
        self.assertEqual(
            set(response.data[0]),
            {
                "user", "username", "first_name", "last_name",
                "file", "uploaded_at", "type",
            },
        )
        self.assertEqual(response.data[0]["user"], self.user.pk)
        self.assertEqual(response.data[0]["type"], "customer")

    def test_business_can_read_customer_list_without_being_listed(self):
        self.authenticate_business_reader()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [profile["user"] for profile in response.data],
            [self.user.pk],
        )

    def authenticate_business_reader(self):
        business = get_user_model().objects.create_user(
            username="business_list_reader",
        )
        UserProfile.objects.create(
            user=business,
            type=UserProfile.AccountType.BUSINESS,
        )
        token = Token.objects.create(user=business)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_customer_list_without_profiles_returns_empty_list(self):
        self.profile.delete()
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


class BusinessProfileListAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="business_list_user",
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            type=UserProfile.AccountType.BUSINESS,
        )
        self.token = Token.objects.create(user=self.user)
        self.url = "/api/profiles/business/"

    def test_business_list_without_token_is_rejected(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_business_list_returns_documented_fields(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assert_business_profile(response)

    def assert_business_profile(self, response):
        self.assertEqual(
            set(response.data[0]),
            {
                "user", "username", "first_name", "last_name",
                "file", "location", "tel", "description",
                "working_hours", "type",
            },
        )
        self.assertEqual(response.data[0]["user"], self.user.pk)
        self.assertEqual(response.data[0]["type"], "business")

    def test_customer_can_read_business_list_without_being_listed(self):
        self.authenticate_customer_reader()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [profile["user"] for profile in response.data],
            [self.user.pk],
        )

    def authenticate_customer_reader(self):
        customer = get_user_model().objects.create_user(
            username="customer_list_reader",
        )
        UserProfile.objects.create(
            user=customer,
            type=UserProfile.AccountType.CUSTOMER,
        )
        token = Token.objects.create(user=customer)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_business_list_without_profiles_returns_empty_list(self):
        self.profile.delete()
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
