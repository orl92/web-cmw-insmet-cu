from django.contrib.auth.models import Group, User
from django.test import TestCase

from apps.accounts.models import GroupProfile, Profile


class ProfileModelTests(TestCase):
    def test_profile_created_via_signal_when_user_created(self):
        user = User.objects.create_user('signaluser', 'signal@example.com', 'password')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertFalse(user.profile.is_ldap)

    def test_profile_str_returns_username(self):
        user = User.objects.create_user('stuser', 'st@example.com', 'password')
        self.assertEqual(str(user.profile), 'stuser')

    def test_profile_uuid_is_unique(self):
        user1 = User.objects.create_user('u1', 'u1@example.com', 'password')
        user2 = User.objects.create_user('u2', 'u2@example.com', 'password')
        self.assertNotEqual(user1.profile.uuid, user2.profile.uuid)

    def test_get_avatar_returns_static_default_when_no_avatar(self):
        user = User.objects.create_user('noavatar', 'no@example.com', 'password')
        avatar = user.profile.get_avatar()
        self.assertIn('avatar.png', avatar)


class GroupProfileModelTests(TestCase):
    def test_group_profile_created_via_signal_when_group_created(self):
        group = Group.objects.create(name='TestGroup')
        self.assertTrue(hasattr(group, 'groupprofile'))

    def test_group_profile_str_returns_group_name(self):
        group = Group.objects.create(name='TestGroup2')
        self.assertEqual(str(group.groupprofile), 'TestGroup2')
