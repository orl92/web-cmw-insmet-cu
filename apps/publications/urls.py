from django.urls import path

from apps.publications.views import (
    ScientificPublicationCreateView,
    ScientificPublicationDeleteView,
    ScientificPublicationDetailView,
    ScientificPublicationListView,
    ScientificPublicationPDFView,
    ScientificPublicationUpdateView,
)

app_name = 'publications'

urlpatterns = [
    path('', ScientificPublicationListView.as_view(), name='list'),
    path('crear/', ScientificPublicationCreateView.as_view(), name='create'),
    path('<uuid:uuid>/editar/', ScientificPublicationUpdateView.as_view(), name='update'),
    path('<uuid:uuid>/eliminar/', ScientificPublicationDeleteView.as_view(), name='delete'),
    path('<uuid:uuid>/', ScientificPublicationDetailView.as_view(), name='detail'),
    path('<uuid:uuid>/pdf/', ScientificPublicationPDFView.as_view(), name='pdf'),
]
