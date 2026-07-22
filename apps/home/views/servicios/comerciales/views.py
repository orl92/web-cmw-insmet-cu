from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import FormView, ListView

from apps.dashboard.forms.suscripciones.forms import PaymentMethodForm
from apps.dashboard.models import Customer, Service, ServiceSubscription


class CommercialServicesListView(LoginRequiredMixin, ListView):
    model = ServiceSubscription
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mis Servicios Comerciales'
        context['parent'] = 'servicios'
        context['segment'] = 'comerciales'
        return context


class PublicCommercialServicesListView(ListView):
    model = Service
    template_name = 'pages/home/servicios/comerciales/servicios_comerciales_public.html'
    context_object_name = 'services'
    paginate_by = 10

    def get_queryset(self):
        return Service.objects.filter(service_type=Service.COMMERCIAL).order_by('title')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Servicios Comerciales'
        context['parent'] = 'servicios'
        context['segment'] = 'comercial_p'
        context['now'] = timezone.now()
        if self.request.user.is_authenticated and hasattr(self.request.user, 'customer'):
            customer = self.request.user.customer
            subs = ServiceSubscription.objects.filter(customer=customer)
            context['user_subscriptions'] = {sub.service_id: sub for sub in subs}
        else:
            context['user_subscriptions'] = {}
        return context


class ServiceDetailView(LoginRequiredMixin, FormView):
    template_name = 'pages/home/servicios/comerciales/detalle_servicio.html'
    form_class = PaymentMethodForm
    success_url = reverse_lazy('dashboard:suscripcion_list')

    def dispatch(self, request, *args, **kwargs):
        self.service = get_object_or_404(Service, uuid=kwargs['uuid'], service_type=Service.COMMERCIAL)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        context['title'] = self.service.title
        context['parent'] = 'servicios'
        context['segment'] = 'comerciales'
        context['estimated_total'] = self.service.price * 30 if self.service.price else 0

        if self.request.user.is_authenticated and hasattr(self.request.user, 'customer'):
            customer = self.request.user.customer
            existing = ServiceSubscription.objects.filter(
                customer=customer,
                service=self.service
            ).exclude(payment_status='expired').first()
            context['existing_subscription'] = existing
        return context

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and hasattr(request.user, 'customer')):
            messages.error(request, "Debes ser un cliente registrado para solicitar servicios.")
            return redirect('{}?next={}'.format(reverse('login:in'), request.path))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        customer = self.request.user.customer
        existing = ServiceSubscription.objects.filter(
            customer=customer,
            service=self.service
        ).exclude(payment_status='expired').first()
        if existing:
            messages.warning(self.request, "Ya tienes una solicitud o suscripción para este servicio.")
            return redirect('home:services_commercial_detail', uuid=self.service.uuid)

        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

        if end_date < start_date:
            messages.error(self.request, "La fecha de fin no puede ser anterior a la de inicio.")
            return self.form_invalid(form)

        ServiceSubscription.objects.create(
            customer=customer,
            service=self.service,
            start_date=start_date,
            end_date=end_date,
            payment_status='requested',
            payment_method=form.cleaned_data['payment_method']
        )
        messages.success(self.request, "Solicitud enviada. El staff generará una factura.")
        return redirect(self.success_url)
