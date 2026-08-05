from django.test import TestCase

from apps.home.forms import GifDownloadForm, MeteoDataForm, MeteogramForm, SoundingForm
from apps.meteo.models import Town


class MeteoDataFormTests(TestCase):
    def test_valid_form(self):
        form = MeteoDataForm(
            data={
                'datetime_init': '2025071006',
                'var_name': 'T2',
            }
        )
        self.assertTrue(form.is_valid())

    def test_invalid_datetime_format(self):
        form = MeteoDataForm(
            data={
                'datetime_init': '2025-07-10',
                'var_name': 'T2',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('datetime_init', form.errors)

    def test_invalid_var_name(self):
        form = MeteoDataForm(
            data={
                'datetime_init': '2025071006',
                'var_name': 'INVALID',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('var_name', form.errors)

    def test_all_var_choices_are_valid(self):
        for code, _label in MeteoDataForm.VAR_CHOICES:
            form = MeteoDataForm(
                data={
                    'datetime_init': '2025071006',
                    'var_name': code,
                }
            )
            self.assertTrue(form.is_valid(), msg=f'var_name={code} should be valid')

    def test_empty_form_invalid(self):
        form = MeteoDataForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('datetime_init', form.errors)
        self.assertIn('var_name', form.errors)


class MeteogramFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.town = Town.objects.create(
            name='Florida',
            latitude=21.5,
            longitude=-78.2,
        )

    def test_valid_form(self):
        form = MeteogramForm(
            data={
                'datetime_init': '2025071006',
                'town': self.town.pk,
            }
        )
        self.assertTrue(form.is_valid())

    def test_datetime_init_required(self):
        form = MeteogramForm(data={'town': self.town.pk})
        self.assertFalse(form.is_valid())
        self.assertIn('datetime_init', form.errors)

    def test_town_required(self):
        form = MeteogramForm(data={'datetime_init': '2025071006'})
        self.assertFalse(form.is_valid())
        self.assertIn('town', form.errors)

    def test_invalid_datetime_format(self):
        form = MeteogramForm(
            data={
                'datetime_init': 'abc',
                'town': self.town.pk,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('datetime_init', form.errors)

    def test_town_queryset_ordered_by_name(self):
        b = Town.objects.create(name='B', latitude=22.0, longitude=-77.0)
        a = Town.objects.create(name='A', latitude=21.0, longitude=-78.0)
        qs = MeteogramForm.base_fields['town'].queryset
        self.assertEqual(list(qs), [a, b, self.town])

    def test_empty_form_invalid(self):
        form = MeteogramForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('datetime_init', form.errors)
        self.assertIn('town', form.errors)


class SoundingFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.town = Town.objects.create(
            name='Camagüey',
            latitude=21.391,
            longitude=-77.908,
        )

    def test_valid_form(self):
        form = SoundingForm(
            data={
                'datetime_init': '2025071006',
                'town': self.town.pk,
                't_index': 1,
            }
        )
        self.assertTrue(form.is_valid())

    def test_t_index_default_initial(self):
        form = SoundingForm()
        self.assertEqual(form.fields['t_index'].initial, 1)

    def test_t_index_min_value_valid(self):
        form = SoundingForm(
            data={
                'datetime_init': '2025071006',
                'town': self.town.pk,
                't_index': 1,
            }
        )
        self.assertTrue(form.is_valid())

    def test_t_index_max_value_valid(self):
        form = SoundingForm(
            data={
                'datetime_init': '2025071006',
                'town': self.town.pk,
                't_index': 24,
            }
        )
        self.assertTrue(form.is_valid())

    def test_t_index_below_min(self):
        form = SoundingForm(
            data={
                'datetime_init': '2025071006',
                'town': self.town.pk,
                't_index': 0,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('t_index', form.errors)

    def test_t_index_above_max(self):
        form = SoundingForm(
            data={
                'datetime_init': '2025071006',
                'town': self.town.pk,
                't_index': 25,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('t_index', form.errors)

    def test_invalid_datetime_format(self):
        form = SoundingForm(
            data={
                'datetime_init': 'not_a_date',
                'town': self.town.pk,
                't_index': 1,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('datetime_init', form.errors)

    def test_town_required(self):
        form = SoundingForm(
            data={
                'datetime_init': '2025071006',
                't_index': 1,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('town', form.errors)

    def test_empty_form_invalid(self):
        form = SoundingForm(data={})
        self.assertFalse(form.is_valid())


class GifDownloadFormTests(TestCase):
    def test_valid_dates(self):
        form = GifDownloadForm(
            data={
                'fecha_inicio': '2025071000',
                'fecha_fin': '2025071018',
            }
        )
        self.assertTrue(form.is_valid())

    def test_start_after_end_raises_error(self):
        form = GifDownloadForm(
            data={
                'fecha_inicio': '2025071018',
                'fecha_fin': '2025071000',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('La fecha de inicio no puede ser mayor que la fecha final', str(form.errors))

    def test_range_over_72h_raises_error(self):
        form = GifDownloadForm(
            data={
                'fecha_inicio': '2025071000',
                'fecha_fin': '2025071301',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('3 días', str(form.errors))

    def test_valid_range_exactly_72h(self):
        form = GifDownloadForm(
            data={
                'fecha_inicio': '2025071000',
                'fecha_fin': '2025071300',
            }
        )
        self.assertTrue(form.is_valid())

    def test_invalid_date_format_on_fecha_inicio(self):
        form = GifDownloadForm(
            data={
                'fecha_inicio': 'invalid',
                'fecha_fin': '2025071018',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_inicio', form.errors)

    def test_invalid_date_format_on_fecha_fin(self):
        form = GifDownloadForm(
            data={
                'fecha_inicio': '2025071000',
                'fecha_fin': 'bad',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_fin', form.errors)

    def test_empty_form_invalid(self):
        form = GifDownloadForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_inicio', form.errors)
        self.assertIn('fecha_fin', form.errors)
