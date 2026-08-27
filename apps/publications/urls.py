from django.urls import path

from apps.publications.views import (
    ScientificPublicationCreateView,
    ScientificPublicationDeleteView,
    ScientificPublicationFileDownloadView,
    ScientificPublicationListView,
    ScientificPublicationUpdateView,
)

app_name = 'publications'

urlpatterns = [
    path('', ScientificPublicationListView.as_view(), name='list'),
    path('crear/', ScientificPublicationCreateView.as_view(), name='create'),
    path('<uuid:uuid>/editar/', ScientificPublicationUpdateView.as_view(), name='update'),
    path('<uuid:uuid>/eliminar/', ScientificPublicationDeleteView.as_view(), name='delete'),
    path('<uuid:uuid>/pdf/', ScientificPublicationFileDownloadView.as_view(), name='pdf'),
]
