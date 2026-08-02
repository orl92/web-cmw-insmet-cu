from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from apps.user_auth.models import Profile
from apps.core.models import SiteConfiguration


def _make_user(username, **kwargs):
    """Crea usuario con datos completos para evitar redirect del middleware."""
    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': f'{username}@example.com',
    }
    data.update(kwargs)
    return User.objects.create_user(username, **data)


def disable_maintenance_mode():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


class UserListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.superuser = User.objects.create_superuser('admin', 'admin@example.com', 'password',
                                                       first_name='Admin', last_name='User')
        cls.user = _make_user('regular')
        cls.url = reverse('user_auth:users_list')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_superuser_can_access(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Listado de Usuarios')

    def test_user_with_permission_can_access(self):
        ct = ContentType.objects.get_for_model(User)
        perm = Permission.objects.get(codename='view_user', content_type=ct)
        self.user.user_permissions.add(perm)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class UserCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.superuser = User.objects.create_superuser('admin2', 'admin2@example.com', 'password',
                                                       first_name='Admin', last_name='User')
        cls.url = reverse('user_auth:user_create')

    def test_get_returns_200_for_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_creates_user_and_profile(self):
        self.client.force_login(self.superuser)
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'first_name': 'New',
            'last_name': 'User',
        }
        response = self.client.post(self.url, data, follow=True)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'profile'))


class UserDeleteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.superuser = User.objects.create_superuser('admin3', 'admin3@example.com', 'password',
                                                       first_name='Admin', last_name='User')
        cls.target = _make_user('todelete')

    def _url(self, uuid):
        return reverse('user_auth:user_delete', args=[uuid])

    def test_post_deletes_user(self):
        self.client.force_login(self.superuser)
        target_uuid = self.target.profile.uuid
        response = self.client.post(self._url(target_uuid), follow=True)
        self.assertFalse(User.objects.filter(username='todelete').exists())
        self.assertRedirects(response, reverse('user_auth:users_list'))


class GroupListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.superuser = User.objects.create_superuser('admin4', 'admin4@example.com', 'password',
                                                       first_name='Admin', last_name='User')
        cls.url = reverse('user_auth:groups_list')

    def test_superuser_can_access(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Listado de Grupos')

    def test_list_renders_edit_and_delete_buttons(self):
        group = Group.objects.create(name='Editores')
        self.assertTrue(hasattr(group, 'profile'))
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertContains(response, f'/accounts/group/update/{group.profile.uuid}/')
        self.assertContains(
            response,
            f'data-uuid="{group.profile.uuid}"',
        )
        self.assertContains(response, 'action-btn')


class GroupCreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        disable_maintenance_mode()
        cls.superuser = User.objects.create_superuser('admin5', 'admin5@example.com', 'password',
                                                       first_name='Admin', last_name='User')
        cls.url = reverse('user_auth:group_create')

    def test_post_creates_group_and_groupprofile(self):
        self.client.force_login(self.superuser)
        data = {'name': 'NewGroup'}
        response = self.client.post(self.url, data, follow=True)
        self.assertTrue(Group.objects.filter(name='NewGroup').exists())
        group = Group.objects.get(name='NewGroup')
        self.assertTrue(hasattr(group, 'profile'))


class ProfileDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = _make_user('profilest')
        cls.url = reverse('user_auth:profile_detail')

    def test_login_required(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/accounts/login/?next={self.url}')

    def test_authenticated_user_can_view_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Perfil de Usuario')


class CustomerRegisterViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('user_auth:customer_register')

    def test_get_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_authenticated_user_gets_redirected(self):
        user = _make_user('loggedin')
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('home:services_commercial_public'))
