from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import UserRole

User = get_user_model()


class CustomUserModelTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )
        self.manager_user = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="managerpass123",
        )
        self.employee_user = User.objects.create_user(
            username="employee",
            email="employee@example.com",
            password="employeepass123",
            role=UserRole.EMPLOYEE,
        )

    def test_user_creation(self):
        self.assertEqual(self.admin_user.role, UserRole.ADMIN)
        self.assertTrue(self.admin_user.is_superuser)
        self.assertTrue(self.admin_user.is_staff)

        self.assertEqual(self.manager_user.role, UserRole.MANAGER)
        self.assertFalse(self.manager_user.is_superuser)
        self.assertFalse(self.manager_user.is_staff)

        self.assertEqual(self.employee_user.role, UserRole.EMPLOYEE)
        self.assertFalse(self.employee_user.is_superuser)
        self.assertFalse(self.employee_user.is_staff)

    def test_user_str_method(self):
        expected_str = f"{self.admin_user.get_full_name()} ({self.admin_user.email}) - {self.admin_user.get_role_display()}"
        self.assertEqual(str(self.admin_user), expected_str)

    def test_user_role_properties(self):
        self.assertTrue(self.admin_user.is_admin)
        self.assertTrue(self.manager_user.is_manager)
        self.assertTrue(self.employee_user.is_employee)


class CustomUserAPITests(APITestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse("rest_register")
        self.login_url = reverse("rest_login")
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

    def test_user_signup(self):
        data = {
            "username": "user",
            "email": "user@example.com",
            "password1": "userpass123",
            "password2": "userpass123",
        }

        response = self.client.post(self.signup_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["username"], data["username"])
        self.assertEqual(response.data["user"]["email"], data["email"])
        self.assertEqual(response.data["user"]["role"], UserRole.MANAGER)

    def test_user_login(self):
        response = self.client.post(
            self.login_url, {"email": "admin@example.com", "password": "adminpass123"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)

    def test_user_details(self):
        response = self.client.post(
            self.login_url, {"email": "admin@example.com", "password": "adminpass123"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], self.admin_user.email)
        self.assertEqual(response.data["user"]["role"], self.admin_user.role)

    def test_invalid_login(self):
        response = self.client.post(
            self.login_url, {"email": "wrong@example.com", "password": "wrongpass"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
