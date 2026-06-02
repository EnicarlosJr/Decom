"""Formularios de autenticacao, usuarios internos e convites."""

import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import (
    AccessInvitation,
    Profile,
    get_system_group_label,
    get_system_groups_queryset,
    is_institutional_email,
    set_user_system_groups,
)


User = get_user_model()


FIELD_INPUT_CLASS = (
    ""
)


class SystemGroupMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Exibe grupos do sistema em linguagem singular sem alterar o valor salvo."""

    def label_from_instance(self, obj):
        return get_system_group_label(obj.name)


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
        help_text="Use o endereco institucional autorizado para receber o codigo de acesso.",
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
        help_text="Informe os 6 digitos enviados para o seu e-mail institucional.",
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

    groups = SystemGroupMultipleChoiceField(
        label="Grupos e permissoes",
        queryset=Group.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = AccessInvitation
        fields = (
            "email",
            "expires_at",
            "notes",
            "groups",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].queryset = get_system_groups_queryset()

    def clean_email(self):
        """Restringe convites ao dominio institucional configurado."""
        email = self.cleaned_data["email"].strip().lower()
        if not is_institutional_email(email):
            raise forms.ValidationError("Cadastre apenas e-mails institucionais.")
        return email

    def clean(self):
        """Exige ao menos um grupo/permissao para o primeiro acesso."""
        cleaned_data = super().clean()
        if not cleaned_data.get("groups"):
            raise forms.ValidationError("Selecione ao menos um grupo ou permissao.")
        return cleaned_data


class AccessInvitationSiteForm(forms.Form):
    """Formulario enxuto usado no painel web de convites."""

    email = forms.EmailField(
        label="E-mail institucional",
        help_text="O convite sera enviado para este endereco.",
        widget=forms.EmailInput(
            attrs={
                "class": FIELD_INPUT_CLASS,
                "placeholder": "usuario@ufvjm.edu.br",
                "autocomplete": "email",
                "autocapitalize": "off",
                "spellcheck": "false",
            }
        ),
    )
    notes = forms.CharField(
        label="Observacoes internas",
        help_text="Campo opcional para contexto administrativo.",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "",
                "rows": 4,
                "placeholder": "Curso, turma ou contexto interno.",
            }
        ),
    )

    groups = SystemGroupMultipleChoiceField(
        label="Grupos e permissoes",
        help_text="Selecione um ou mais acessos que serao aplicados ao usuario.",
        queryset=Group.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].queryset = get_system_groups_queryset()

    def clean_email(self):
        """Normaliza e valida o e-mail institucional do convidado."""
        email = self.cleaned_data["email"].strip().lower()
        if not is_institutional_email(email):
            raise forms.ValidationError("Cadastre apenas e-mails institucionais.")
        return email

    def clean(self):
        """Exige ao menos um grupo/permissao para liberar o primeiro acesso."""
        cleaned_data = super().clean()
        if not cleaned_data.get("groups"):
            raise forms.ValidationError("Selecione ao menos um grupo ou permissao.")
        return cleaned_data


class ProfileInstitutionalAccessForm(forms.ModelForm):
    """Formulario para superusuarios ajustarem o perfil de quem ja esta no sistema."""

    groups = SystemGroupMultipleChoiceField(
        label="Grupos e permissoes",
        queryset=Group.objects.none(),
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Profile
        fields = (
            "display_name",
            "institutional_id",
        )
        widgets = {
            "display_name": forms.TextInput(attrs={"class": "", "placeholder": "Nome exibido"}),
            "institutional_id": forms.TextInput(attrs={"class": "", "placeholder": "Matricula, SIAPE ou RA"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["groups"].queryset = get_system_groups_queryset()
        if self.instance and self.instance.pk:
            self.fields["groups"].initial = self.instance.user.groups.filter(
                name__in=[group.name for group in get_system_groups_queryset()]
            )

    def clean(self):
        """Exige ao menos um grupo/permissao para pessoas cadastradas."""
        cleaned_data = super().clean()
        if not cleaned_data.get("groups"):
            raise forms.ValidationError("Selecione ao menos um grupo ou permissao.")
        return cleaned_data

    def save(self, commit=True):
        """Salva os dados complementares e aplica os grupos ao usuario."""
        profile = super().save(commit=commit)
        set_user_system_groups(profile.user, list(self.cleaned_data["groups"]))
        return profile
