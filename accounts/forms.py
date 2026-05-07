"""Formularios de autenticacao, usuarios internos e convites."""

import re

from django import forms
from django.contrib.auth import get_user_model

from .models import AccessInvitation, is_institutional_email


User = get_user_model()


FIELD_INPUT_CLASS = (
    "field-input block w-full rounded-2xl border border-slate-300 "
    "bg-white px-4 py-4 text-slate-900 placeholder-slate-400 shadow-sm "
    "outline-none transition focus:border-gov.blue focus:ring-4 "
    "focus:ring-[rgba(53,91,136,0.12)]"
)


def build_internal_username(email, user_id=None):
    """Gera um username interno estavel a partir do e-mail institucional."""
    local_part = email.split("@", 1)[0].lower().strip()
    slug = re.sub(r"[^a-z0-9._-]+", "-", local_part).strip("-") or "usuario"
    slug = slug[:150]
    candidate = slug
    suffix = 1

    while User.objects.exclude(pk=user_id).filter(username=candidate).exists():
        tail = f"-{suffix}"
        candidate = f"{slug[: 150 - len(tail)]}{tail}"
        suffix += 1

    return candidate


class RequestLoginCodeForm(forms.Form):
    """Formulario para solicitar um codigo temporario de acesso por e-mail."""

    email = forms.EmailField(
        label="E-mail institucional",
        widget=forms.EmailInput(
            attrs={
                "class": FIELD_INPUT_CLASS,
                "placeholder": "nome.sobrenome@ufvjm.edu.br",
                "autocomplete": "email",
                "autocapitalize": "off",
                "spellcheck": "false",
            }
        ),
    )

    def clean_email(self):
        """Aceita apenas e-mails institucionais permitidos."""
        email = self.cleaned_data["email"].strip().lower()
        if not is_institutional_email(email):
            raise forms.ValidationError(
                "Utilize um e-mail institucional autorizado para acessar o sistema."
            )
        return email


class VerifyLoginCodeForm(forms.Form):
    """Formulario para validar o codigo temporario recebido."""

    code = forms.CharField(
        label="Codigo de acesso",
        min_length=6,
        max_length=6,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "class": f"{FIELD_INPUT_CLASS} field-code text-center text-lg tracking-[0.35em]",
                "placeholder": "000000",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
            }
        ),
    )

    def clean_code(self):
        """Garante que o codigo tenha apenas digitos."""
        code = self.cleaned_data["code"].strip()
        if not code.isdigit():
            raise forms.ValidationError("Informe apenas os 6 numeros do codigo.")
        return code


class DepartmentUserCreationForm(forms.ModelForm):
    """Formulario do admin para criar usuarios sem senha local."""

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "is_staff", "is_active")

    def clean_email(self):
        """Valida dominio e unicidade do e-mail institucional."""
        email = self.cleaned_data["email"].strip().lower()
        if not is_institutional_email(email):
            raise forms.ValidationError("Cadastre apenas e-mails institucionais.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ja existe um usuario com este e-mail.")
        return email

    def save(self, commit=True):
        """Cria usuario com senha inutilizavel e username interno derivado."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = build_internal_username(user.email)
        user.set_unusable_password()
        if commit:
            user.save()
        return user


class DepartmentUserChangeForm(forms.ModelForm):
    """Formulario do admin para manutencao de usuarios existentes."""

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "is_staff", "is_active")

    def clean_email(self):
        """Valida dominio e unicidade do e-mail em edicao."""
        email = self.cleaned_data["email"].strip().lower()
        if not is_institutional_email(email):
            raise forms.ValidationError("Cadastre apenas e-mails institucionais.")
        queryset = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("Ja existe um usuario com este e-mail.")
        return email

    def save(self, commit=True):
        """Mantem username interno sincronizado com o e-mail informado."""
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = build_internal_username(user.email, user.pk)
        if commit:
            user.save()
        return user


class AccessInvitationAdminForm(forms.ModelForm):
    """Formulario do admin Django para criar ou editar convites."""

    class Meta:
        model = AccessInvitation
        fields = ("email", "expires_at", "notes")

    def clean_email(self):
        """Restringe convites ao dominio institucional configurado."""
        email = self.cleaned_data["email"].strip().lower()
        if not is_institutional_email(email):
            raise forms.ValidationError("Cadastre apenas e-mails institucionais.")
        return email


class AccessInvitationSiteForm(forms.Form):
    """Formulario enxuto usado no painel web de convites."""

    email = forms.EmailField(
        label="E-mail institucional",
        widget=forms.EmailInput(
            attrs={
                "class": FIELD_INPUT_CLASS,
                "placeholder": "aluno@ufvjm.edu.br",
                "autocomplete": "email",
                "autocapitalize": "off",
                "spellcheck": "false",
            }
        ),
    )
    notes = forms.CharField(
        label="Observacoes",
        required=False,
        widget=forms.Textarea(
            attrs={
                    "class": (
                        "field-input block min-h-28 w-full rounded-2xl border border-slate-300 "
                        "bg-white px-4 py-4 text-slate-900 placeholder-slate-400 shadow-sm "
                        "outline-none transition focus:border-gov.blue focus:ring-4 "
                        "focus:ring-[rgba(53,91,136,0.12)]"
                    ),
                "placeholder": "Turma, curso, observacoes internas ou contexto do convite.",
            }
        ),
    )

    def clean_email(self):
        """Normaliza e valida o e-mail institucional do convidado."""
        email = self.cleaned_data["email"].strip().lower()
        if not is_institutional_email(email):
            raise forms.ValidationError("Cadastre apenas e-mails institucionais.")
        return email
