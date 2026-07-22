import uuid

from django.core.validators import FileExtensionValidator
from django.db import models

from apps.common.utils import FileHandlerMixin, pdf_upload_path


class ScientificPublication(FileHandlerMixin, models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=200, verbose_name="Título")
    author = models.ForeignKey("Author", on_delete=models.CASCADE, related_name="authored_publications", verbose_name="Autor")
    coauthors = models.ManyToManyField("Author", related_name="coauthored_publications", verbose_name="Coautores", blank=True)
    publication_date = models.DateField(verbose_name="Fecha de Publicación")
    summary = models.TextField(verbose_name="Resumen")
    pdf_file = models.FileField(upload_to=pdf_upload_path, validators=[FileExtensionValidator(["pdf"])], verbose_name="Archivo PDF")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    file_fields = ['pdf_file']

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Publicación Científica"
        verbose_name_plural = "Publicaciones Científicas"
        ordering = ["-publication_date"]
        default_permissions = ()
        permissions = (
            ("view_scientific_publication", "Ver"),
            ("add_scientific_publication", "Añadir"),
            ("change_scientific_publication", "Editar"),
            ("delete_scientific_publication", "Eliminar"),
        )


class Author(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    first_name = models.CharField(max_length=100, verbose_name="Nombres")
    last_name = models.CharField(max_length=100, verbose_name="Apellidos")
    email = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    institution = models.CharField(max_length=200, blank=True, verbose_name="Institución")
    orcid_id = models.CharField(max_length=19, blank=True, verbose_name="ID ORCID")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Autor"
        verbose_name_plural = "Autores"
        ordering = ["last_name", "first_name"]
        default_permissions = ()
        permissions = (
            ("view_author", "Ver"),
            ("add_author", "Añadir"),
            ("change_author", "Editar"),
            ("delete_author", "Eliminar"),
        )
