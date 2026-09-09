from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, IntegerField, When
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, ListView

from apps.commercial.forms import PaymentMethodForm
from apps.commercial.models import Customer, Service, ServiceSubscription


class CommercialServicesListView(LoginRequiredMixin, ListView):
    model = ServiceSubscription
    template_name = 'pages/home/services/commercial.html'
    context_object_name = 'subscriptions'
    paginate_by = 10

    STATUS_RIBBONS = {
        'activo': 'bg-green',
        'pendiente de pago': 'bg-orange',
        'solicitado': 'bg-blue',
        'expirado': 'bg-red',
    }

    def get_queryset(self):
        try:
            customer = self.request.user.commercial_customer
        except Customer.DoesNotExist:
            return ServiceSubscription.objects.none()
        return (
            ServiceSubscription.objects.filter(customer=customer, record_active=True)
            .select_related('service', 'service__user')
            .order_by(
                Case(
                    When(payment_status='requested', then=0),
                    When(payment_status='pending', then=1),
                    When(payment_status='paid', then=2),
                    default=3,
                    output_field=IntegerField(),
                ),
                '-start_date',
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mis Servicios'
        context['parent'] = 'servicios'
        context['segment'] = 'comerciales'
        context['status_ribbon'] = self.STATUS_RIBBONS
        return context


class PublicCommercialServicesListView(ListView):
    model = Service
    template_name = 'pages/home/services/commercial_public.html'
    context_object_name = 'services'
    paginate_by = 10

    def get_queryset(self):
        return Service.objects.filter(
            service_type=Service.COMMERCIAL, record_active=True
        ).order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Comerciales'
        context['parent'] = 'servicios'
        context['segment'] = 'comercial_p'
        return context


class ServiceDetailView(LoginRequiredMixin, FormView):
    template_name = 'pages/home/services/service_detail.html'
    form_class = PaymentMethodForm
    success_url = reverse_lazy('commercial:suscripcion_list')

    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(
            Service,
            uuid=kwargs['uuid'],
            service_type=Service.COMMERCIAL,
            record_active=True,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        context['title'] = self.service.title
        context['parent'] = 'servicios'
        context['segment'] = 'comerciales'
        price = self.service.price
        context['estimated_total'] = price * 1 if price else 0
        context['billing_period'] = self.service.get_billing_period_display()
        # El precio crudo se expone vía context['service'].price; el template
        # compone el formato con el filtro format_cup (fase 3).
        context['related_services'] = (
            Service.objects.filter(
                service_type=Service.COMMERCIAL, record_active=True
            )
            .exclude(uuid=self.service.uuid)
            .order_by('title')[:4]
        )

        if self.request.user.is_authenticated and hasattr(self.request.user, 'commercial_customer'):
            customer = self.request.user.commercial_customer
            subs = ServiceSubscription.objects.filter(customer=customer, service=self.service)
            in_flight = (
                subs.filter(payment_status__in=['requested', 'pending'])
                .order_by('-start_date')
                .first()
            )
            active = (
                subs.filter(
                    payment_status='paid',
                    end_date__gt=timezone.now(),
                )
                .order_by('-start_date')
                .first()
            )
            context['in_flight_subscription'] = in_flight
            context['active_subscription'] = active
        return context

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['category'] = self.service.service_category
        return kwargs

    def post(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and hasattr(request.user, 'commercial_customer')):
            messages.error(request, 'Debes ser un cliente registrado para solicitar servicios.')
            return redirect('{}?next={}'.format(reverse('user_auth:login'), request.path))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        customer = self.request.user.commercial_customer
        existing = (
            ServiceSubscription.objects.filter(customer=customer, service=self.service)
            .filter(payment_status__in=['requested', 'pending'])
            .first()
        )
        if existing:
            messages.warning(
                self.request, 'Ya tienes una solicitud o suscripción para este servicio.'
            )
            return redirect('home:services_commercial_detail', uuid=self.service.uuid)

        start_date = form.cleaned_data['start_date']
        quantity = form.cleaned_data['quantity']
        end_date = Service.compute_end_date(start_date, quantity, self.service.service_category)

        ServiceSubscription.objects.create(
            customer=customer,
            service=self.service,
            start_date=start_date,
            end_date=end_date,
            quantity=quantity,
            payment_status='requested',
            payment_method=form.cleaned_data['payment_method'],
        )
        messages.success(self.request, 'Solicitud enviada. El staff generará una factura.')
        return redirect(self.success_url)
