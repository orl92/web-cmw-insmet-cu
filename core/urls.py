"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from common.utils import My400View, My403View, My404View, My500View, test_400, test_403, test_404, test_500


urlpatterns = [
    path('', include('login.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    
    
    path('test-400/', test_400, name='test_400'),
    path('test-403/', test_403, name='test_403'),
    path('test-404/', test_404, name='test_404'),
    path('test-500/', test_500, name='test_500'),
    
    path('', include('home.urls')),
]

handler400 = My400View.as_view()
handler403 = My403View.as_view()
handler404 = My404View.as_view()
handler500 = My500View.as_view()

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

