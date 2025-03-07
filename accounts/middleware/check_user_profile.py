from django.contrib import messages
from django.contrib.auth.middleware import get_user
from django.shortcuts import redirect
from django.urls import reverse


class CheckUserProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = get_user(request)
        if user.is_authenticated:
            try:
                profile = user.profile
                if not user.email or not user.first_name or not user.last_name:
                    if request.path != reverse('update_profile', kwargs={'uuid': profile.uuid}):
                        messages.warning(request, 'Por favor, complete su perfil antes de continuar.')
                        return redirect(reverse('update_profile', kwargs={'uuid': profile.uuid}))
            except user.profile.RelatedObjectDoesNotExist:
                if request.path != reverse('update_profile', kwargs={'uuid': user.uuid}):
                    messages.warning(request, 'Por favor, complete su perfil antes de continuar.')
                    return redirect(reverse('update_profile', kwargs={'uuid': user.uuid}))
        return self.get_response(request)
