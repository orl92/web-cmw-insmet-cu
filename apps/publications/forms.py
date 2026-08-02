from django import forms

from apps.publications.models import Author, ScientificPublication


class ScientificPublicationForm(forms.ModelForm):
    author_first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nombres del autor"}
        ),
        label="Nombres del Autor",
        required=True,
    )

    author_last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Apellidos del autor"}
        ),
        label="Apellidos del Autor",
        required=True,
    )

    author_email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Correo electrónico del autor",
            }
        ),
        label="Correo del Autor",
        required=False,
    )

    author_institution = forms.CharField(
        max_length=200,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Institución del autor"}
        ),
        label="Institución del Autor",
        required=False,
    )

    author_orcid_id = forms.CharField(
        max_length=19,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "ORCID ID del autor"}
        ),
        label="ORCID ID del Autor",
        required=False,
    )

    class Meta:
        model = ScientificPublication
        fields = ["title", "publication_date", "summary", "pdf"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Título de la publicación científica",
                }
            ),
            "publication_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "summary": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Resumen de la publicación",
                    "rows": 4,
                }
            ),
            "pdf": forms.FileInput(
                attrs={"class": "form-control", "accept": ".pdf"}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and hasattr(self.instance, "author"):
            self.fields["author_first_name"].initial = self.instance.author.first_name
            self.fields["author_last_name"].initial = self.instance.author.last_name
            self.fields["author_email"].initial = self.instance.author.email
            self.fields["author_institution"].initial = self.instance.author.institution
            self.fields["author_orcid_id"].initial = self.instance.author.orcid_id

    def clean(self):
        cleaned_data = super().clean()
        author_first_name = cleaned_data.get("author_first_name")
        author_last_name = cleaned_data.get("author_last_name")

        if not author_first_name or not author_last_name:
            raise forms.ValidationError(
                "El autor principal debe tener al menos nombre y apellido."
            )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        author_first_name = self.cleaned_data.get("author_first_name")
        author_last_name = self.cleaned_data.get("author_last_name")
        author_email = self.cleaned_data.get("author_email")

        author_data = {
            "first_name": author_first_name,
            "last_name": author_last_name,
            "email": author_email,
            "institution": self.cleaned_data.get("author_institution", ""),
            "orcid_id": self.cleaned_data.get("author_orcid_id", ""),
        }

        {k: v for k, v in author_data.items() if v}

        if author_email:
            author, created = Author.objects.get_or_create(
                email=author_email, defaults=author_data
            )
        else:
            author, created = Author.objects.get_or_create(
                first_name=author_first_name,
                last_name=author_last_name,
                defaults=author_data,
            )

        if not created:
            for key, value in author_data.items():
                if value:
                    setattr(author, key, value)
            author.save()

        instance.author = author

        if self.user:
            instance.user = self.user

        if commit:
            instance.save()

        return instance


class CoauthorForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "email", "institution", "orcid_id"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombres"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Apellidos"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Correo electrónico"}
            ),
            "institution": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Institución"}
            ),
            "orcid_id": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ORCID ID"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = False
        self.fields["institution"].required = False
        self.fields["orcid_id"].required = False

        if self.instance and self.instance.pk:
            self.fields["id"].initial = self.instance.pk

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name")
        last_name = cleaned_data.get("last_name")

        if not first_name or not last_name:
            if first_name or last_name or cleaned_data.get("email"):
                raise forms.ValidationError(
                    "El coautor debe tener al menos nombre y apellido."
                )

        return cleaned_data

    def save(self, commit=True):
        instance_id = self.cleaned_data.get("id")

        if instance_id:
            try:
                author = Author.objects.get(pk=instance_id)
                author.first_name = self.cleaned_data.get("first_name")
                author.last_name = self.cleaned_data.get("last_name")
                author.email = self.cleaned_data.get("email")
                author.institution = self.cleaned_data.get("institution")
                author.orcid_id = self.cleaned_data.get("orcid_id")
                if commit:
                    author.save()
                return author
            except Author.DoesNotExist:
                pass

        first_name = self.cleaned_data.get("first_name")
        last_name = self.cleaned_data.get("last_name")
        email = self.cleaned_data.get("email")

        if not first_name or not last_name:
            return None

        author_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "institution": self.cleaned_data.get("institution", ""),
            "orcid_id": self.cleaned_data.get("orcid_id", ""),
        }

        if email:
            author, created = Author.objects.get_or_create(
                email=email, defaults=author_data
            )
        else:
            author, created = Author.objects.get_or_create(
                first_name=first_name, last_name=last_name, defaults=author_data
            )

        if not created:
            for key, value in author_data.items():
                if value:
                    setattr(author, key, value)
            if commit:
                author.save()

        return author
