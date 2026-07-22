from django.contrib import admin

from apps.publications.models import Author, ScientificPublication

admin.site.register(ScientificPublication)
admin.site.register(Author)
