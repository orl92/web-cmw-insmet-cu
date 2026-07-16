from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LoginViewTests(TestCase):
    def test_login_page_returns_200(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_with_valid_credentials(self):
        User.objects.create_user('logintest', 'login@example.com', 'password',
                                 first_name='Test', last_name='User')
        response = self.client.post(reverse('login'), {
            'username': 'logintest',
            'password': 'password',
        }, follow=True)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_with_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'nonexistent',
            'password': 'wrong',
        }, follow=True)
        self.assertFalse(response.context['user'].is_authenticated)


class LogoutViewTests(TestCase):
    def test_logout_redirects_to_index(self):
        user = User.objects.create_user('logouttest', 'logout@example.com', 'password',
                                        first_name='Test', last_name='User')
        self.client.force_login(user)
        response = self.client.get(reverse('logout'), follow=True)
        self.assertRedirects(response, reverse('index'))
