from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic import View

from dashboard.models import Customer
from dashboard.models import Service, ServiceSubscription


# Create your views here.


class CommercialServicesListView(LoginRequiredMixin, ListView):
    model = ServiceSubscription  # Cambiamos a Suscripción
    template_name = 'pages/home/servicios/comerciales/servicios_comerciales.html'
    context_object_name = 'subscriptions'
    paginate_by = 10

    def get_queryset(self):
        try:
            customer = self.request.user.customer
        except Customer.DoesNotExist:
            return ServiceSubscription.objects.none()
        ahora = timezone.now()
        return ServiceSubscription.objects.filter(
            customer=customer,
            payment_status='paid',
            end_date__gt=ahora
        ).select_related('service', 'service__user').order_by('start_date')


class PublicCommercialServicesListView(ListView):
    model = Service
    template_name = 'pages/home/servicios/comerciales/servicios_comerciales_public.html'
    context_object_name = 'services'
    paginate_by = 10

    def get_queryset(self):
        return Service.objects.filter(service_type=Service.COMMERCIAL).order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Catalogo Servicios Comerciales'
        context['now'] = timezone.now()
        if self.request.user.is_authenticated and hasattr(self.request.user, 'customer'):
            customer = self.request.user.customer
            subs = ServiceSubscription.objects.filter(customer=customer)
            context['user_subscriptions'] = {sub.service_id: sub for sub in subs}
        else:
            context['user_subscriptions'] = {}
        return context

class RequestSubscriptionView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return (self.request.user.groups.filter(name='Clientes').exists() and
                hasattr(self.request.user, 'customer'))

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "No tienes un perfil de cliente. Regístrate como empresa.")
            return redirect('customer_register')
        else:
            messages.info(self.request, "Debes iniciar sesión como cliente.")
            return redirect('{}?next={}'.format(reverse('login'), self.request.path))

    def get(self, request, *args, **kwargs):
        service_uuid = kwargs.get('uuid')
        service = get_object_or_404(Service, uuid=service_uuid, service_type=Service.COMMERCIAL)
        customer = request.user.customer

        existing = ServiceSubscription.objects.filter(
            customer=customer,
            service=service
        ).exclude(payment_status='expired').first()

        if existing:
            if existing.payment_status == 'paid' and existing.end_date > timezone.now():
                messages.warning(request, "Ya tienes una suscripción activa para este servicio.")
            elif existing.payment_status == 'pending':
                messages.info(request, "Ya tienes una factura pendiente de pago.")
            elif existing.payment_status == 'requested':
                messages.info(request, "Ya has solicitado este servicio.")
            else:
                return redirect('renovar_suscripcion', uuid=existing.uuid)
            return redirect('public_servicios_comerciales')

        ServiceSubscription.objects.create(
            customer=customer,
            service=service,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            payment_status='requested'
        )
        messages.success(request, "Solicitud enviada. El staff generará una factura.")
        return redirect('listado_suscripciones')
