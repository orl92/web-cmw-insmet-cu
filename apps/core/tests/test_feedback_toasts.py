"""Tests for 021-feedback-toasts: Django messages rendered as toasts.

Verifies that the toast blocks in ``layouts/dashboard.html`` and
``layouts/home.html`` render Django messages as ``showToast(...)`` calls (not
fixed Bootstrap ``.alert`` blocks), with correct type mapping, ``escapejs`` XSS
safety, ``extra_tags='danger'`` override, and that redirect-stored messages
survive to the next page load.

The full layouts are rendered with ``render_to_string(..., request=request)``
so the message context processor and template tags (perm_filters, branding)
receive a real ``request.user`` instead of ``None``.
"""

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.template.loader import render_to_string
from django.test import TestCase
from django.test.client import RequestFactory

from apps.core.models import SiteConfiguration

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(user, message_list):
    """Build a request with session, authenticated user, and messages storage.

    ``message_list`` is a list of ``Message`` objects. Attaching a
    ``FallbackStorage`` with the messages mirrors what Django's
    ``MessageMiddleware`` does with session-stored messages on a page load.
    """
    request = RequestFactory().get('/dashboard/')
    session = SessionStore()
    session.create()
    request.session = session
    request.user = user
    storage = FallbackStorage(request)
    for msg in message_list:
        storage.add(msg.level, msg.message, msg.extra_tags)
    request._messages = storage
    return request


def _render(layout, request):
    return render_to_string(
        layout,
        {'title': 'Test', 'parent': 'Test'},
        request=request,
    )


def _make_message(level, text, extra_tags=''):
    from django.contrib.messages.storage.base import Message

    return Message(level, text, extra_tags=extra_tags)


def _base_user():
    return User.objects.create_user(
        'toast_user',
        'toast@example.com',
        'password',
        first_name='Toast',
        last_name='Test',
        is_staff=True,
        is_superuser=True,
    )


def _configure_site():
    SiteConfiguration.objects.get_or_create(defaults={'maintenance_mode': False})


def _resolved_types(html):
    """Simulate JS resolution to return the toast types rendered in `html`.

    The inline block defines ``var _toastMap = {success: "success", ...};``
    then per visible message calls ``showToast("<msg>", _toastMap["<key>"] ||
    "info", 5000)``. ``message.level_tag`` is the ``<key>``; the runtime type
    is ``_toastMap[<key>]`` (falling back to ``"info"``). This helper evaluates
    that lookup like the browser would, returning the list of toast types in
    render order.
    """
    import re

    # 1. Parse the _toastMap definition to map key -> toast type value.
    def_map = re.search(r'_toastMap\s*=\s*\{(.*?)\};', html)
    map_lookup = {}
    if def_map:
        for key, value in re.findall(r'(\w+)\s*:\s*"([^"]+)"', def_map.group(1)):
            map_lookup[key] = value

    # 2. Parse each showToast call's second argument. It is either a literal
    #    `"type"` (from extra_tags='danger') or `_toastMap["<key>"] || "info"`.
    types = []
    for type_arg in re.findall(r'_toastMap\["(\w+)"\]\s*\|\|\s*"info"', html):
        types.append(map_lookup.get(type_arg, 'info'))
    types += re.findall(r'showToast\([^)]*",\s*"(\w+)"', html)
    return types


def _assert_toast_type(testcase, html, text, expected_type):
    """Assert that `html` renders a toast for `text` using `expected_type`."""
    testcase.assertIn('showToast(', html)
    testcase.assertIn(text, html)
    testcase.assertIn(expected_type, _resolved_types(html))


# ---------------------------------------------------------------------------
# Toast rendering per message level
# ---------------------------------------------------------------------------


class ToastLevelMappingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _configure_site()
        cls.user = _base_user()

    def test_success_renders_toast(self):
        request = _make_request(
            self.user, [_make_message(messages.SUCCESS, 'Guardado correctamente')]
        )
        html = _render('layouts/dashboard.html', request)
        _assert_toast_type(self, html, 'Guardado correctamente', 'success')

    def test_error_maps_to_danger(self):
        request = _make_request(self.user, [_make_message(messages.ERROR, 'Ha ocurrido un error')])
        html = _render('layouts/dashboard.html', request)
        _assert_toast_type(self, html, 'Ha ocurrido un error', 'danger')

    def test_warning_maps_to_warning(self):
        request = _make_request(self.user, [_make_message(messages.WARNING, 'Verifique los datos')])
        html = _render('layouts/dashboard.html', request)
        _assert_toast_type(self, html, 'Verifique los datos', 'warning')

    def test_info_maps_to_info(self):
        request = _make_request(self.user, [_make_message(messages.INFO, 'Nota informativa')])
        html = _render('layouts/dashboard.html', request)
        _assert_toast_type(self, html, 'Nota informativa', 'info')

    def test_extra_tags_danger_overrides_success(self):
        request = _make_request(
            self.user, [_make_message(messages.SUCCESS, 'Logo eliminado', extra_tags='danger')]
        )
        html = _render('layouts/dashboard.html', request)
        # extra_tags='danger' overrides the SUCCESS (success) mapping.
        _assert_toast_type(self, html, 'Logo eliminado', 'danger')
        self.assertNotIn('success', _resolved_types(html))


# ---------------------------------------------------------------------------
# Redirect-stored message survives (messages framework path)
# ---------------------------------------------------------------------------


class RedirectMessageSurvivesTests(TestCase):
    """A message added during a view (stored in the session on redirect) must
    render as a toast on the next page load.

    Django's ``MessageMiddleware`` stores the message in the session during
    the redirect response and, on the following request, wraps it back into
    ``request._messages`` (FallbackStorage). We simulate exactly that path: the
    message lives in storage attached to the incoming request, and the
    dashboard/home layout turns it into a ``showToast(...)`` call.
    """

    @classmethod
    def setUpTestData(cls):
        _configure_site()
        cls.user = _base_user()

    def test_redirect_message_survives(self):
        request = _make_request(
            self.user, [_make_message(messages.SUCCESS, 'Guardado correctamente')]
        )
        html = _render('layouts/dashboard.html', request)
        _assert_toast_type(self, html, 'Guardado correctamente', 'success')


# ---------------------------------------------------------------------------
# XSS safety
# ---------------------------------------------------------------------------


class EscapeJsSafetyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _configure_site()
        cls.user = _base_user()

    def test_escapejs_prevents_script_injection(self):
        evil = '</script><script>alert(1)</script>'
        request = _make_request(self.user, [_make_message(messages.SUCCESS, evil)])
        html = _render('layouts/dashboard.html', request)
        # escapejs encodes < as \u003C and > as \u003E, so the raw closing
        # script tag must never appear inside the inline script body.
        self.assertNotIn('</script><script>alert(1)</script>', html)
        self.assertIn('\\u003C/script\\u003E', html)


# ---------------------------------------------------------------------------
# No .alert remnants
# ---------------------------------------------------------------------------


class NoAlertRemnantsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _configure_site()
        cls.user = _base_user()

    def test_no_alert_class_from_messages(self):
        request = _make_request(
            self.user,
            [
                _make_message(messages.SUCCESS, 'Todo bien'),
                _make_message(messages.ERROR, 'Algo falló'),
            ],
        )
        html = _render('layouts/dashboard.html', request)
        self.assertNotIn('class="alert', html)
        self.assertNotIn('alert-dismissible', html)


# ---------------------------------------------------------------------------
# home.html layout
# ---------------------------------------------------------------------------


class HomeTemplateToastTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        _configure_site()
        cls.user = _base_user()

    def test_home_renders_toast(self):
        request = _make_request(self.user, [_make_message(messages.SUCCESS, 'Mensaje de home')])
        html = _render('layouts/home.html', request)
        self.assertIn('showToast(', html)
        self.assertIn('Mensaje de home', html)
        self.assertNotIn('class="alert', html)
        self.assertNotIn('alert-dismissible', html)
