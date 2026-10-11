"""La fecha del contrato debe ser el día local, nunca el día UTC.

La facturación por lote ya no crea contratos: la fecha propuesta para un
contrato nuevo la calcula `ContractForm` con `timezone.localdate()` (y el
comando de datos de prueba usa el mismo cálculo). Si alguien la cambiara a
`timezone.now().date()`, entre las 20:00 y las 23:59 hora local la fecha UTC ya
pertenece al día siguiente y el contrato quedaría fechado en el día futuro: un
documento legal con fecha por delante.

Se congela el reloj dentro de esa ventana para que el test sea determinista y
no dependa de la hora en que corra la suite.
"""

from datetime import UTC, datetime
from unittest.mock import patch

from django.urls import reverse

from apps.commercial.models import Contract
from apps.commercial.tests.test_invoice_regeneration import RegenerarCasoBase


class ContractLocaldateTests(RegenerarCasoBase):
    # UTC 2026-10-04T02:30 == Havana 2026-10-03 22:30. La fecha UTC ya rodó.
    FIXED_UTC = datetime(2026, 10, 4, 2, 30, 0, tzinfo=UTC)
    LOCAL_DATE = datetime(2026, 10, 3).date()
    UTC_DATE = datetime(2026, 10, 4).date()

    def test_contract_generated_in_the_evening_is_dated_today_not_tomorrow(self):
        with patch('django.utils.timezone.now', return_value=self.FIXED_UTC):
            from django.utils import timezone

            # Guarda la premisa: este instante cae dentro de la ventana.
            self.assertEqual(timezone.localdate(), self.LOCAL_DATE)
            self.assertNotEqual(timezone.localdate(), self.UTC_DATE)

            # El formulario propone la fecha (local) y el contrato se guarda
            # con ese valor: quien cambie la derivación a la fecha UTC deja
            # un contrato fechado mañana dentro de esta ventana.
            url = reverse('commercial:contrato_create')
            formulario = self.client.get(url)
            self.assertEqual(formulario.status_code, 200)
            inicio = formulario.context['form'].fields['start_date'].initial

            response = self.client.post(
                url,
                {
                    'customer': self.customer.pk,
                    'number': 'CONT-LOCAL-001',
                    'start_date': inicio.isoformat(),
                    'validity_years': '2',
                },
            )

        self.assertEqual(response.status_code, 302)

        contract = Contract.objects.get(number='CONT-LOCAL-001')
        self.assertEqual(
            contract.start_date,
            self.LOCAL_DATE,
            msg='El contrato se fechó con el día UTC; en la ventana de 20:00-23:59 '
            'eso produce un contrato con fecha futura.',
        )
