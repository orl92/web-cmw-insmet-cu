"""Verification tests for the user_auth profile update form template.

Asserts that the avatar image must not open in a blank tab and instead uses
the vendored fslightbox (data-fslightbox). Templates are NOT modified.

The profile middleware (CheckUserProfileMiddleware) redirects incomplete
profiles, so the superuser must have email/first_name/last_name set, and the
Profile must carry an avatar for the fslightbox link to render.

NOTE: the base layout footer intentionally keeps ``target="_blank"`` on its
social-media links — out of scope — so we assert the *avatar anchor* does not
use ``target="_blank"`` rather than the whole page.
"""

import base64
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.user_auth.models import Profile

User = get_user_model()

PNG_BYTES = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)


def assert_file_anchor_not_blank_tab(test_case, content, file_url):
    needle = ('href="' + file_url + '" target="_blank"').encode()
    test_case.assertNotIn(needle, content)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ProfileFilePreviewModalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin4', 'admin4@example.com', 'pass')
        self.user.first_name = 'Admin'
        self.user.last_name = 'Test'
        self.user.email = 'admin4@example.com'
        self.user.save()

        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.avatar = SimpleUploadedFile('av.png', PNG_BYTES, 'image/png')
        profile.save()

    def test_profile_update_no_blank_tab_and_fslightbox(self):
        self.client.force_login(self.user)
        url = reverse('user_auth:profile_update')
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'documentPdfModal', resp.content)
        self.assertIn(b'data-fslightbox', resp.content)
        assert_file_anchor_not_blank_tab(self, resp.content, self.user.profile.get_avatar())
