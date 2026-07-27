from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from apps.user_auth.forms.users import UserForm, UserUpdateForm


class UserFormTests(TestCase):
    def test_valid_data_creates_user(self):
        form = UserForm(data={
            'username': 'formuser',
            'email': 'form@example.com',
            'password1': 'Complex123!',
            'password2': 'Complex123!',
        })
        self.assertTrue(form.is_valid())

    def test_blank_data_is_invalid(self):
        form = UserForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('password1', form.errors)

    def test_password_mismatch_is_invalid(self):
        form = UserForm(data={
            'username': 'mismatch',
            'email': 'm@example.com',
            'password1': 'Complex123!',
            'password2': 'DifferentPass1!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)


class UserUpdateFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('updateuser', 'update@example.com', 'password')

    def test_valid_data(self):
        form = UserUpdateForm(data={
            'username': 'updateduser',
            'email': 'updated@example.com',
        }, instance=self.user)
        self.assertTrue(form.is_valid())
