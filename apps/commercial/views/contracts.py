from django.contrib import messages
from django.contrib.admin.models import ADDITION, DELETION
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, View

from apps.commercial.forms.contract import ContractForm
from apps.commercial.models import Contract
from apps.core.utils import log_action


class ContractListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Contract
    template_name = 'pages/commercial/contract/list.html'
    permission_required = 'commercial.view_contract'

    def get_queryset(self):
        # `customer__user` porque la columna Cliente muestra `display_name`,
        # que para una persona natural lee los nombres del User.
        return Contract.objects.select_related(
            'subscription__customer__user', 'subscription__service'
        ).all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Contratos'
        context['parent'] = ''
        context['segment'] = 'contratos'
        context['btn'] = 'Añadir Contrato'
        context['url_create'] = reverse_lazy('commercial:contrato_create')
        context['url_list'] = reverse_lazy('commercial:contrato_list')
        context['is_superuser'] = self.request.user.is_superuser
        context['objects'] = self.get_queryset()
        return context


class ContractCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'pages/commercial/contract/create.html'
    permission_required = 'commercial.add_contract'
    success_url = reverse_lazy('commercial:contrato_list')
    url_redirect = success_url

    def form_valid(self, form):
        response = super().form_valid(form)
        log_action(
            user=self.request.user,
            obj=self.object,
            action_flag=ADDITION,
            message=(
                f'Contrato {self.object.number} creado para '
                f'{self.object.subscription.customer.company_name}.'
            ),
        )
        messages.success(self.request, 'Contrato creado con éxito.', extra_tags='success')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Contrato'
        context['parent'] = ''
        context['segment'] = 'contratos'
        context['url_list'] = self.success_url
        return context


class ContractDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Contract
    template_name = 'pages/commercial/contract/detail.html'
    permission_required = 'commercial.view_contract'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Contract.objects.select_related(
                'subscription__customer__user', 'subscription__service'
            ),
            uuid=self.kwargs['uuid'],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Detalle del Contrato'
        context['parent'] = ''
        context['segment'] = 'contratos'
        context['url_list'] = reverse_lazy('commercial:contrato_list')
        return context


class ContractDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'commercial.delete_contract'

    def post(self, request, uuid):
        contract = get_object_or_404(Contract, uuid=uuid)
        if not contract.record_active:
            messages.warning(request, 'El contrato ya estaba desactivado.')
            return redirect('commercial:contrato_list')
        contract.delete()
        log_action(
            user=self.request.user,
            obj=contract,
            action_flag=DELETION,
            message=f'Contrato desactivado: {contract.number}.',
        )
        messages.success(request, 'Contrato desactivado con éxito.')
        return redirect('commercial:contrato_list')


class ContractHardDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Eliminación física de contrato (solo superusuarios)."""

    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, uuid):
        contract = get_object_or_404(Contract, uuid=uuid)
        contract_number = contract.number
        contract.hard_delete()
        log_action(
            user=request.user,
            obj=contract,
            action_flag=DELETION,
            message=f'Contrato {contract_number} eliminado físicamente.',
        )
        messages.success(request, f'Contrato {contract_number} eliminado permanentemente.')
        return redirect('commercial:suscripcion_list')
