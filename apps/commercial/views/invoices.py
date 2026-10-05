import json
import logging
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.html import escape
from django.views.generic import FormView, ListView, View

from apps.commercial.forms.invoice import (
    InvoiceCostAllocationFormSet,
    InvoiceForm,
    InvoiceItemFormSet,
)
from apps.commercial.models import (
    Contract,
    Customer,
    Invoice,
    InvoiceCostAllocation,
    InvoiceItem,
    Service,
    ServiceSubscription,
)
from apps.commercial.views.invoice_utils import (
    _prefill_cost_allocations_from_items,
    enviar_correo_factura,
)
from apps.core.models import CompanySettings
from apps.core.tasks import generate_invoice_pdf_and_email_task
from apps.core.utils import log_action
from apps.core.views import ServeModelFileView

logger = logging.getLogger(__name__)


class InvoiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Invoice
    template_name = 'pages/commercial/invoice/list.html'
    context_object_name = 'objects'
    permission_required = 'commercial.view_invoice'

    def get_queryset(self):
        # `with_display_status` trae items_total/items_paid anotados para que la
        # columna Estado no dispare una consulta por fila. `customer__user` viene
        # en el select_related porque la columna Cliente muestra `display_name`,
        # que para una persona natural lee los nombres del User.
        return (
            Invoice.objects.select_related(
                'customer__user', 'subscription__customer__user', 'subscription__service'
            )
            .prefetch_related('items')
            .with_display_status()
            .order_by('-issue_date')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Listado de Facturas'
        context['parent'] = 'facturacion'
        context['segment'] = 'facturas'
        context['btn'] = 'Añadir Factura'
        context['url_create'] = reverse_lazy('commercial:factura_create')
        context['url_list'] = reverse_lazy('commercial:factura_list')
        context['is_superuser'] = self.request.user.is_superuser
        return context


class InvoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'pages/commercial/invoice/create.html'
    form_class = InvoiceForm
    permission_required = 'commercial.add_invoice'
    success_url = reverse_lazy('commercial:factura_list')

    def get_initial(self):
        initial = super().get_initial()
        today = timezone.now().date()
        regenerar = self.suscripcion_a_regenerar()
        customer_uuid = self.request.GET.get('customer_uuid')
        if customer_uuid:
            try:
                customer = Customer.objects.get(uuid=customer_uuid)
                initial['customer'] = customer
                # La suscripción a regenerar manda en las fechas propuestas: es la
                # que el operador está por volver a facturar.
                pending_sub = (
                    regenerar
                    if regenerar and regenerar.customer_id == customer.pk
                    else ServiceSubscription.objects.filter(
                        customer=customer,
                        payment_status__in=['requested', 'pending'],
                        start_date__isnull=False,
                    ).first()
                )
                if pending_sub:
                    # El periodo facturado lo fija el operador en el formulario,
                    # no la suscripción: ésta ya no tiene expiración que sugiera
                    # uno. Se propone desde la fecha de inicio que eligió el
                    # cliente, que sí es un dato conocido y coherente.
                    inicio = pending_sub.start_date.date() if pending_sub.start_date else today
                    initial['start_date'] = inicio.isoformat()
                    initial['end_date'] = (inicio + timedelta(days=30)).isoformat()
                else:
                    initial['start_date'] = today.isoformat()
                    initial['end_date'] = (today + timedelta(days=30)).isoformat()
            except Customer.DoesNotExist:
                pass
        else:
            initial['start_date'] = today.isoformat()
            initial['end_date'] = (today + timedelta(days=30)).isoformat()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Factura'
        context['parent'] = 'facturacion'
        context['segment'] = 'facturas'
        context['url_list'] = reverse_lazy('commercial:factura_list')
        context['items_formset'] = InvoiceItemFormSet(prefix='items')
        context['cost_allocations_formset'] = (
            kwargs['cost_allocations_formset']
            if 'cost_allocations_formset' in kwargs
            else self.cost_allocations_formset()
        )
        context['regenerar_sub'] = self.suscripcion_a_regenerar()
        commercial_services = Service.objects.filter(service_type=Service.COMMERCIAL)
        # The manual lines need `service_category` to tell months from days, and
        # the browser cannot derive the unit from the dates alone.
        context['commercial_services_json'] = json.dumps(
            list(commercial_services.values('id', 'code', 'title', 'price', 'service_category')),
            cls=DjangoJSONEncoder,
        )
        context['company'] = CompanySettings.get_instance()
        return context

    def suscripcion_a_regenerar(self):
        """Suscripción que el operador pidió regenerar, si el pedido es válido.

        `regenerar` llega en el GET y vuelve en el POST (el formulario lo
        reenvía en un campo oculto), así que se lee de los dos. Se valida en
        ambos casos: una suscripción inexistente o ya pagada no tiene factura que
        regenerar, y en ese caso el formulario abre normal en vez de prometer
        una anulación que no va a pasar.
        """
        uuid = self.request.GET.get('regenerar') or self.request.POST.get('regenerar')
        if not uuid:
            return None
        subscription = (
            ServiceSubscription.objects.filter(uuid=uuid, record_active=True)
            .select_related('service')
            .first()
        )
        if subscription is None or subscription.payment_status == 'paid':
            return None
        return subscription

    def _save_cost_allocations(self, invoice, cost_formset):
        """Guarda la imputación de la factura ya creada.

        Se persiste a mano y no con `formset.save()` porque en este punto la
        factura existe recién, y un formset atado a la línea no puede resolver la
        FK hacia algo que todavía no estaba en la base cuando se validó. Son de
        dos a tres filas: no vale la pena el indirecto de un inline formset para
        eso. `full_clean` va explícito porque `Model.save()` no valida, y la regla
        del porcentaje vive en el `clean()` del modelo.
        """
        if cost_formset is None:
            return
        for form in cost_formset.forms:
            if not hasattr(form, 'cleaned_data') or form.cleaned_data.get('DELETE'):
                continue
            fila = InvoiceCostAllocation(
                invoice=invoice,
                codigo=form.cleaned_data['codigo'],
                porcentaje=form.cleaned_data['porcentaje'],
            )
            fila.full_clean()
            fila.save()

    def cost_allocations_formset(self):
        """Formset de imputación a centros de costo.

        En el POST va ligado a lo enviado. En el GET se precarga desde los
        servicios del cliente cuando ya se sabe cuál es —el caso de regenerar
        una factura— porque sin cliente no hay códigos de los que deducir un
        centro, y un reparto inventado sería peor que uno vacío.
        """
        prefix = 'cost_allocations'
        if self.request.method == 'POST':
            return InvoiceCostAllocationFormSet(self.request.POST, prefix=prefix)
        return InvoiceCostAllocationFormSet(prefix=prefix, initial=self._prefill_inicial())

    def _prefill_inicial(self):
        subscription = self.suscripcion_a_regenerar()
        if subscription is None:
            return []
        return _prefill_cost_allocations_from_items(
            [InvoiceItem(codigo=subscription.service.code or '')]
        )

    def form_valid(self, form):
        customer = form.cleaned_data['customer']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        commercial_registry = form.cleaned_data['commercial_registry']
        subscriptions = form.cleaned_data.get('subscriptions')
        regenerar = self.suscripcion_a_regenerar()

        # La imputación se valida antes de crear la factura: si el reparto no
        # suma 100 % no debe quedar una factura a medias en la base, y el error
        # tiene que volver al formulario en vez de perderse en un redirect.
        cost_formset = self.cost_allocations_formset()
        if not cost_formset.is_valid():
            messages.error(self.request, 'Corrige el reparto entre centros de costo de la factura.')
            return self.render_to_response(
                self.get_context_data(form=form, cost_allocations_formset=cost_formset)
            )

        if subscriptions and subscriptions.exists():
            # El periodo facturado es único y viene del formulario: la suscripción
            # ya no tiene fecha de expiración que propose uno propio, así que
            # todas las seleccionadas se facturan en el mismo periodo en vez de
            # agruparse por un dato que ya no existe.
            nueva = self.process_batch_invoice(
                customer, start_date, end_date, commercial_registry, subscriptions, cost_formset
            )
            messages.success(
                self.request,
                f'Se generó la factura del período {start_date.strftime("%d/%m/%Y")} - '
                f'{end_date.strftime("%d/%m/%Y")}.',
            )
            # Después de crear, nunca antes: la factura anterior sólo se anula
            # cuando su reemplazo ya existe.
            self.anular_factura_previa(regenerar, subscriptions, [nueva])
            return redirect(self.success_url)
        else:
            # Facturación manual: crea suscripciones nuevas, así que la
            # suscripción regenerada no está en esta factura y no hay nada que
            # reemplazar. Se avisa en vez de anular a ciegas.
            self.anular_factura_previa(regenerar, subscriptions)
            return self.process_manual_invoice(
                form, customer, start_date, end_date, commercial_registry, cost_formset
            )

    def anular_factura_previa(self, regenerar, subscriptions, nuevas_facturas=None):
        """Anula la factura que la nueva reemplaza, sólo si la nueva la reemplaza.

        Va después de crear la factura nueva a propósito: el defecto que
        reportaba el operador no era "se anuló la factura equivocada" sino "se
        anuló antes de que existiera el reemplazo". Si algo falla antes de acá,
        la factura anterior sigue viva.

        No se envuelve en `transaction.atomic`: la tarea de PDF se encola dentro
        de `process_batch_invoice`, y con la transacción abierta el worker
        podría renderizar contra filas todavía sin confirmar. El orden ya da la
        garantía que importa: crear primero, anular después.
        """
        if regenerar is None:
            return
        incluida = subscriptions and subscriptions.filter(pk=regenerar.pk).exists()
        if not incluida:
            messages.warning(
                self.request,
                'La suscripción a regenerar no se facturó en esta factura: su factura '
                'anterior no se anuló y su certificado sigue vigente.',
            )
            return

        # `Invoice.subscription` es un ancla opcional, así que `for_subscription`
        # cubre las facturas de lote por el vínculo de línea. Las nuevas se
        # excluyen explícitamente: en el caso de un solo período la factura
        # recién creada también cuelga de la suscripción.
        nuevas_ids = [invoice.pk for invoice in nuevas_facturas or []]
        anteriores = (
            Invoice.objects.for_subscription(regenerar)
            .exclude(pk__in=nuevas_ids)
            .filter(is_cancelled=False)
        )
        numeros = []
        for invoice in anteriores:
            invoice.is_cancelled = True
            invoice.save(update_fields=['is_cancelled'])
            numeros.append(invoice.number)
            log_action(
                user=self.request.user,
                obj=invoice,
                action_flag=CHANGE,
                message=f'Factura {invoice.number} anulada al confirmar la factura nueva',
                request=self.request,
            )

        # `Certificate` es `SoftDeleteModel` y `QuerySet.delete()` ignora su
        # `delete()`: borra la fila de verdad y deja el PDF huérfano en `media/`.
        # Por eso se da de baja uno por uno: baja lógica (la trazabilidad del
        # certificado emitido se conserva) y `_cleanup_files()` borra el archivo,
        # que es lo que corresponde a un documento que ya no vale. `hard_delete()`
        # además sería peor: el certificado se le entregó al cliente.
        certificados = regenerar.certificates.filter(record_active=True)
        dados_de_baja = 0
        for certificado in certificados:
            certificado.delete()
            dados_de_baja += 1
        if dados_de_baja:
            log_action(
                user=self.request.user,
                obj=regenerar,
                action_flag=CHANGE,
                message=(
                    f'{dados_de_baja} certificado(s) dado(s) de baja al confirmar la factura nueva'
                ),
                request=self.request,
            )

        if numeros:
            messages.success(
                self.request,
                f'Factura anterior anulada ({", ".join(numeros)}) al confirmar la nueva.',
            )

    def anchor_invoice(self, invoice, subscriptions):
        """Cuelga la factura de la suscripción cuando hay una sola.

        `Invoice.subscription` es un atajo de conveniencia: con varias
        suscripciones no hay una respuesta única, así que se deja en NULL y el
        vínculo real queda en cada línea. Cuando hay exactamente una se
        completa, porque `subscription.invoices` es la relación que consulta
        buena parte del código.
        """
        unique = {sub.pk: sub for sub in subscriptions}
        if len(unique) == 1:
            invoice.subscription = next(iter(unique.values()))
            invoice.save(update_fields=['subscription'])
        return invoice

    def process_batch_invoice(
        self,
        customer,
        start_date,
        end_date,
        commercial_registry,
        subscriptions,
        cost_formset=None,
    ):
        """Crea la factura de un período y la devuelve.

        El retorno lo usa `form_valid`: al regenerar, la factura anterior se
        anula por diferencia, así que hay que saber cuáles son las nuevas para
        no dejar el reemplazo anulado junto con lo que reemplaza.
        """
        invoice = Invoice.objects.create(
            subscription=None, customer=customer, amount=0, number=self.generate_invoice_number()
        )
        total = 0
        items = []
        for sub in subscriptions:
            price = sub.service.price or 0
            quantity = sub.quantity
            amount = price * quantity
            unidad_medida = 'MES' if sub.service.service_category == 'agrometeo' else 'DÍA'
            item = InvoiceItem.objects.create(
                invoice=invoice,
                subscription=sub,
                codigo=sub.service.code or '',
                descripcion=sub.service.title,
                cantidad=quantity,
                unidad_medida=unidad_medida,
                precio=price,
                importe=amount,
            )
            items.append(item)
            total += amount

            # La suscripción conserva la fecha de inicio que eligió quien la
            # solicitó: es un dato del contrato con el cliente, no del periodo
            # facturado, y sobreescribirlo lo convertía en un valor derivado de
            # la factura. Al facturar sólo cambia el estado de pago. El periodo
            # facturado es de la factura, no de la suscripción: las
            # suscripciones no vencen por tiempo.
            sub.payment_status = 'pending'
            sub.save()

            contract, created = Contract.objects.get_or_create(
                subscription=sub,
                defaults={
                    'number': self.generate_contract_number(),
                    'date': timezone.now().date(),
                    'commercial_registry': commercial_registry,
                },
            )
            if not created:
                contract.commercial_registry = commercial_registry
                contract.save(update_fields=['commercial_registry'])

            log_action(
                user=self.request.user,
                obj=sub,
                action_flag=CHANGE,
                message=(
                    f'Suscripción facturada en lote: {sub.service.title} '
                    f'para {sub.customer.company_name}'
                ),
            )

        invoice.amount = total
        invoice.save()
        self.anchor_invoice(invoice, subscriptions)

        log_action(
            user=self.request.user,
            obj=invoice,
            action_flag=ADDITION,
            message=(
                f'Factura por lote {invoice.number} - Cliente: '
                f'{customer.company_name} - Monto: ${total:.2f}'
            ),
            request=self.request,
        )

        # Las asignaciones se guardan antes del task: el PDF se genera aparte,
        # y si no estuvieran ya en la base saldría sin imputación.
        self._save_cost_allocations(invoice, cost_formset)
        site_url = self.request.build_absolute_uri('/')
        generate_invoice_pdf_and_email_task(str(invoice.uuid), site_url)
        return invoice

    def process_manual_invoice(
        self, form, customer, start_date, end_date, commercial_registry, cost_formset=None
    ):
        items_formset = InvoiceItemFormSet(self.request.POST, prefix='items')
        if not items_formset.is_valid():
            messages.error(self.request, 'Corrige los errores en las líneas de factura.')
            context = self.get_context_data(form=form)
            context['items_formset'] = items_formset
            return self.render_to_response(context)

        invoice = Invoice.objects.create(
            subscription=None, customer=customer, amount=0, number=self.generate_invoice_number()
        )
        total = 0
        items = []
        created_subs = []

        for item_form in items_formset:
            if item_form.cleaned_data and not item_form.cleaned_data.get('DELETE', False):
                cd = item_form.cleaned_data
                service = cd['service']
                cantidad = cd['cantidad']
                unidad_medida = 'MES' if service.service_category == 'agrometeo' else 'DÍA'

                sub = ServiceSubscription.objects.create(
                    customer=customer,
                    service=service,
                    start_date=timezone.make_aware(
                        datetime.combine(start_date, datetime.min.time())
                    ),
                    payment_status='pending',
                    record_active=True,
                    quantity=cantidad,
                )

                created_subs.append(sub)

                item = InvoiceItem.objects.create(
                    invoice=invoice,
                    subscription=sub,
                    codigo=cd.get('codigo', service.code or ''),
                    descripcion=service.title,
                    cantidad=cantidad,
                    unidad_medida=cd.get('unidad_medida') or unidad_medida,
                    precio=cd['precio'],
                    importe=cantidad * cd['precio'],
                )
                items.append(item)
                total += cantidad * cd['precio']

                log_action(
                    user=self.request.user,
                    obj=sub,
                    action_flag=ADDITION,
                    message=(
                        f'Suscripción creada manualmente: {customer.company_name} - {service.title}'
                    ),
                )

        invoice.amount = total
        invoice.save()
        self.anchor_invoice(invoice, created_subs)

        log_action(
            user=self.request.user,
            obj=invoice,
            action_flag=ADDITION,
            message=(
                f'Factura manual {invoice.number} - Cliente: '
                f'{customer.company_name} - Monto: ${total:.2f}'
            ),
            request=self.request,
        )

        # Las asignaciones se guardan antes del task: el PDF se genera aparte,
        # y si no estuvieran ya en la base saldría sin imputación.
        self._save_cost_allocations(invoice, cost_formset)
        site_url = self.request.build_absolute_uri('/')
        generate_invoice_pdf_and_email_task(str(invoice.uuid), site_url)
        messages.success(self.request, 'Factura manual generada (con suscripciones creadas).')
        return redirect(self.success_url)

    def generate_invoice_number(self):
        year = timezone.now().year
        last = Invoice.objects.filter(issue_date__year=year).order_by('-issue_date').first()
        if last and last.number:
            try:
                num = int(last.number.split('-')[-1])
                return f'{year}-{num + 1:04d}'
            except ValueError, IndexError:
                pass
        return f'{year}-0001'

    def generate_contract_number(self):
        year = timezone.now().year
        last_contract = Contract.objects.filter(date__year=year).order_by('-date').first()
        if last_contract and last_contract.number:
            try:
                num = int(last_contract.number.split('-')[-1])
                return f'{year}-{num + 1:04d}'
            except ValueError, IndexError:
                pass
        return f'{year}-0001'


class InvoicePDFDownloadView(ServeModelFileView):
    model = Invoice
    field = 'pdf'
    permission_required = 'commercial.view_invoice'

    def get_queryset(self):
        return super().get_queryset().select_related('subscription')

    def get_permission_required(self, obj):
        """Staff con permiso, o el cliente titular de la factura.

        El cliente ve sus PDFs en "Mis Suscripciones" (dashboard) y en el
        portal; sin esto los botones Ver PDF/Descargar de sus propias facturas
        devuelven 403 porque no tienen ``commercial.view_invoice``.
        """
        user = self.request.user
        if not hasattr(user, 'commercial_customer'):
            return self.permission_required
        customer = user.commercial_customer
        if obj.customer_id == customer.pk:
            return None
        if obj.subscription_id and obj.subscription.customer_id == customer.pk:
            return None
        return self.permission_required

    def get_filename(self, obj):
        return f'factura_{obj.number}_{obj.issue_date:%Y-%m-%d}.pdf'

    def get(self, request, uuid):
        invoice = self.get_object()
        perm = self.get_permission_required(invoice)
        if perm and not request.user.has_perm(perm):
            raise PermissionDenied
        if not getattr(invoice, self.field):
            # El PDF se genera por una tarea Huey; si no existe (p. ej. el
            # worker no corre en dev) lo generamos bajo demanda para no
            # ocultar los botones de Descargar / Ver PDF en el listado.
            self._generate_pdf_if_missing(invoice)
        return super().get(request, uuid)

    def _generate_pdf_if_missing(self, invoice):
        from apps.commercial.views.invoice_utils import generate_invoice_pdf_standalone

        customer = invoice.customer
        items = list(invoice.items.all())
        # El período sale de `invoice.period_label` con respaldo en `issue_date`;
        # la regeneración bajo demanda usa exactamente el mismo camino que la
        # tarea asíncrona, así que las dos imprimen el mismo período.
        try:
            generate_invoice_pdf_standalone(invoice, customer, items)
            invoice.refresh_from_db(fields=[self.field])
        except Exception as exc:  # pragma: no cover - depends on WeasyPrint/Pango
            logger.exception(
                'Fallo la generación bajo demanda del PDF de la factura %s: %s',
                invoice.uuid,
                exc,
            )


class CancelInvoiceView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'commercial.delete_invoice'

    def post(self, request, uuid):
        invoice = get_object_or_404(Invoice, uuid=uuid)

        if invoice.is_cancelled:
            messages.warning(request, f'La factura {invoice.number} ya estaba anulada.')
            return redirect('commercial:factura_list')

        invoice.is_cancelled = True
        invoice.save()

        items_with_subs = invoice.items.filter(subscription__isnull=False).select_related(
            'subscription'
        )
        for item in items_with_subs:
            sub = item.subscription
            if sub.payment_status in ['pending', 'requested']:
                sub.payment_status = 'requested'
                sub.save()
                log_action(
                    user=request.user,
                    obj=sub,
                    action_flag=CHANGE,
                    message=(
                        f"Estado revertido a 'solicitado' por anulación de factura {invoice.number}"
                    ),
                )

        log_action(
            user=request.user,
            obj=invoice,
            action_flag=CHANGE,
            message=f'Factura {invoice.number} anulada',
        )
        messages.success(request, f'Factura {invoice.number} anulada correctamente.')
        return redirect('commercial:factura_list')


class RetryInvoicePdfView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Vuelve a encolar el render del PDF sin reenviar el correo.

    El PDF se genera en una tarea Huey asíncrona, así que una factura puede
    quedar pagada sin PDF (el worker caído, un render fallido) y no hay forma
    de impedirlo sin volver síncrono el envío. Lo que sí tiene que existir es
    la reparación: reencolar sólo el paso del PDF, que es idempotente y no
    duplica el correo si el de la factura ya salió.
    """

    permission_required = 'commercial.change_invoice'

    def post(self, request, uuid):
        invoice = get_object_or_404(Invoice, uuid=uuid)

        if invoice.pdf_ready:
            messages.warning(request, f'La factura {invoice.number} ya tiene su PDF.')
            return redirect('commercial:factura_list')
        if invoice.is_cancelled:
            messages.warning(
                request, f'No se genera el PDF de una factura anulada ({invoice.number}).'
            )
            return redirect('commercial:factura_list')

        site_url = request.build_absolute_uri('/')
        generate_invoice_pdf_and_email_task(str(invoice.uuid), site_url, solo_paso='pdf')
        log_action(
            user=request.user,
            obj=invoice,
            action_flag=CHANGE,
            message=f'Reencolado el PDF de la factura {invoice.number}',
            request=request,
        )
        messages.success(
            request,
            f'Generación del PDF de la factura {invoice.number} reencolada.',
        )
        return redirect('commercial:factura_list')


class InvoiceHardDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, uuid):
        invoice = get_object_or_404(Invoice, uuid=uuid)
        invoice_number = invoice.number
        log_action(
            user=request.user,
            obj=invoice,
            action_flag=DELETION,
            message=f'Factura {invoice.number} eliminada permanentemente',
        )
        invoice.hard_delete()
        messages.success(request, f'Factura {invoice_number} eliminada permanentemente.')
        return redirect('commercial:factura_list')


class ResendInvoiceEmailView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'commercial.change_invoice'

    def get(self, request, uuid):
        invoice = get_object_or_404(Invoice, uuid=uuid)

        customer = None
        if invoice.subscription:
            customer = invoice.subscription.customer
        elif invoice.customer:
            customer = invoice.customer
        else:
            first_item = invoice.items.first()
            if first_item and first_item.subscription:
                customer = first_item.subscription.customer

        if not customer or not customer.user or not customer.user.email:
            messages.error(
                request, 'No se pudo determinar el cliente o no tiene correo electrónico.'
            )
            return redirect('commercial:factura_list')

        exito = enviar_correo_factura(invoice, customer, request=request)
        if exito:
            messages.success(
                request, f'Correo de la factura {invoice.number} reenviado correctamente.'
            )
        else:
            messages.error(
                request,
                f'No se pudo reenviar el correo de la factura {invoice.number}. Revise los logs.',
            )
        return redirect('commercial:factura_list')


@login_required
@permission_required('commercial.view_subscription')
def ajax_pending_subscriptions(request):
    customer_id = request.GET.get('customer')
    if not customer_id:
        return HttpResponse('')
    qs = ServiceSubscription.objects.filter(
        customer_id=customer_id, payment_status__in=['requested', 'pending'], record_active=True
    ).select_related('service')
    if not request.user.is_staff and not request.user.is_superuser:
        qs = qs.filter(customer__user=request.user)
    subs = qs
    if not subs.exists():
        return HttpResponse('<p class="text-muted">No hay suscripciones pendientes.</p>')
    html = ''
    for sub in subs:
        start_str = sub.start_date.strftime('%Y-%m-%d') if sub.start_date else ''
        title = escape(sub.service.title or '')
        summary = escape(sub.service.summary or '')
        unidad = escape(sub.get_quantity_period_display())
        # El periodo facturado no viaja por acá: lo fija el operador en el
        # formulario. La suscripción sólo aporta su inicio y la cantidad que
        # multiplica al precio, así que no hay `data-end` ni `data-days` que
        # calcular.
        html += f'''
        <div class="form-check">
          <input class="form-check-input subscription-check" type="checkbox"
                 name="subscriptions" value="{sub.pk}"
                 id="sub_{sub.pk}" data-start="{start_str}"
                 data-quantity="{sub.quantity}"
                 data-unidad="{unidad}"
                 data-service="{title}" data-summary="{summary}">
          <label class="form-check-label" for="sub_{sub.pk}">
            <strong>{title}</strong> <span class="text-muted">({unidad})</span>
            <br><small class="text-muted">{summary}</small>
          </label>
        </div>
        '''
    return HttpResponse(html)
