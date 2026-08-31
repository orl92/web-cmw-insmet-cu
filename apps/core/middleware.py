from django.contrib import messages
from django.contrib.auth.middleware import get_user
from django.shortcuts import redirect
from django.urls import reverse

from apps.core.models import SiteConfiguration
from apps.user_auth.models import Profile


class CheckUserProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = get_user(request)
        if user.is_authenticated:
            profile, created = Profile.objects.get_or_create(user=user)

            missing_personal = not user.email or not user.first_name or not user.last_name

            missing_company = False
            if hasattr(user, 'commercial_customer'):
                customer = user.commercial_customer
                required_fields = ['account', 'agency_bank', 'address', 'phone']
                if customer.client_type == customer.ClientType.JURIDICA:
                    required_fields += ['company_name', 'reeup', 'nit']
                for field in required_fields:
                    if not (getattr(customer, field, '') or '').strip():
                        missing_company = True
                        break

            if missing_personal or missing_company:
                update_url = reverse('user_auth:profile_update')
                if request.path != update_url:
                    if missing_company:
                        messages.warning(
                            request,
                            'Por favor, complete los datos de su cliente antes de continuar.',
                        )
                    else:
                        messages.warning(
                            request, 'Por favor, complete su perfil antes de continuar.'
                        )
                    return redirect(update_url)

        return self.get_response(request)


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        site_config = SiteConfiguration.objects.first()
        # Reuse the singleton fetch for the rest of the request (e.g. the
        # site_branding context processor) to avoid a redundant DB query.
        request.site_config = site_config
        if (
            request.user.is_authenticated
            and not request.user.is_superuser
            and site_config
            and site_config.maintenance_mode
            and request.path not in [reverse('user_auth:login'), reverse('user_auth:logout')]
        ):
            messages.warning(request, 'El sitio está en modo mantenimiento.')
            return redirect('user_auth:login')
        return self.get_response(request)
