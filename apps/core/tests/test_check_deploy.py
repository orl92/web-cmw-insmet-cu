"""
Tests for the deployment system-check gate (change 013-check-deploy-ci).

These tests are written FIRST (RED phase) for the settings hardening that makes
`python manage.py check --deploy --fail-level WARNING` green on a fresh checkout
(no ``.env``, ``DEBUG`` defaults to ``False``). They lock the two security
invariants required so the new ``deploy-check`` CI job does not fail:

- ``X_FRAME_OPTIONS`` must be ``'DENY'`` (resolves security.W019 for real).
- ``security.W008`` must be silenced because Nginx terminates TLS and performs
  the HTTPS redirect, so Django intentionally leaves ``SECURE_SSL_REDIRECT``
  as ``False``.
"""

from django.conf import settings
from django.test import TestCase


class XFrameOptionsTests(TestCase):
    """REQ: X_FRAME_OPTIONS is hardened to 'DENY' (security.W019)."""

    def test_x_frame_options_is_deny(self):
        """settings.X_FRAME_OPTIONS MUST equal 'DENY' (clickjacking hardening)."""
        self.assertEqual(settings.X_FRAME_OPTIONS, 'DENY')

    def test_xframe_middleware_is_present(self):
        """The clickjacking middleware that emits the X-Frame-Options header is active."""
        self.assertIn(
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            settings.MIDDLEWARE,
        )

    def test_frame_ancestors_is_self_not_none(self):
        """CSP frame-ancestors stays 'self' so DENY aligns with the CSP boundary."""
        self.assertEqual(
            settings.CONTENT_SECURITY_POLICY['DIRECTIVES']['frame-ancestors'],
            ["'self'"],
        )


class W008SilencingTests(TestCase):
    """REQ: security.W008 is intentionally silenced and documented."""

    def test_w008_is_silenced(self):
        """'security.W008' MUST be in settings.SILENCED_SYSTEM_CHECKS."""
        self.assertIn('security.W008', settings.SILENCED_SYSTEM_CHECKS)

    def test_ssl_redirect_not_true(self):
        """SECURE_SSL_REDIRECT must NOT be True (Nginx owns the HTTPS redirect)."""
        self.assertIsNot(getattr(settings, 'SECURE_SSL_REDIRECT', False), True)
