from django.contrib import messages
from django.contrib.auth.middleware import get_user
from django.shortcuts import redirect
from django.urls import reverse
from accounts.models import Profile


class CheckUserProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = get_user(request)
        if user.is_authenticated:
            # Garantizar que el perfil existe (por señal debería, pero por si acaso)
            profile, created = Profile.objects.get_or_create(user=user)
            profile_uuid = profile.uuid

            # 1. Datos personales
            missing_personal = not user.email or not user.first_name or not user.last_name

            # 2. Datos de empresa (si es cliente)
            missing_company = False
            if hasattr(user, 'customer'):
                customer = user.customer
                required_fields = ['company_name', 'reeup', 'nit', 'account', 'address', 'phone']
                for field in required_fields:
                    if not getattr(customer, field, '').strip():
                        missing_company = True
                        break

            if missing_personal or missing_company:
                update_url = reverse('update_profile', kwargs={'uuid': profile_uuid})
                if request.path != update_url:
                    if missing_company:
                        messages.warning(request, 'Por favor, complete los datos de su empresa antes de continuar.')
                    else:
                        messages.warning(request, 'Por favor, complete su perfil antes de continuar.')
                    return redirect(update_url)

        return self.get_response(request)
