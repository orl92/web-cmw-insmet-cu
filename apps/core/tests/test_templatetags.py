from decimal import Decimal

from django.template import Context, Template
from django.test import TestCase

from apps.core.templatetags.utils_filters import format_cup


class FormatCupFilterTest(TestCase):
    def test_decimal_with_thousands_separator(self):
        self.assertEqual(format_cup(Decimal('1234.56')), '$1.234,56')

    def test_small_decimal_uses_comma_for_decimals(self):
        self.assertEqual(format_cup(Decimal('45.50')), '$45,50')

    def test_integer_gets_two_decimals(self):
        self.assertEqual(format_cup(1234), '$1.234,00')

    def test_float_gets_two_decimals(self):
        self.assertEqual(format_cup(45.5), '$45,50')

    def test_none_returns_zero(self):
        self.assertEqual(format_cup(None), '$0,00')

    def test_empty_string_returns_zero(self):
        self.assertEqual(format_cup(''), '$0,00')

    def test_zero_returns_zero(self):
        self.assertEqual(format_cup(0), '$0,00')

    def test_available_via_my_filters_template_tag(self):
        rendered = Template('{% load my_filters %}{{ price|format_cup }}').render(
            Context({'price': Decimal('1234.56')}),
        )
        self.assertEqual(rendered, '$1.234,56')
