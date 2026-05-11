


from datetime import timedelta
import secrets
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.urls import reverse

# Obtém o modelo de usuário (pode ser customizado no projeto)
User = get_user_model()


def is_institutional_email(email):
    """
    Verifica se o e-mail pertence ao domínio institucional configurado.
    Ex: se o domínio for 'ufvjm.edu.br', só aceita emails desse domínio.
    """
    domain = getattr(settings, "DEPARTMENT_ALLOWED_EMAIL_DOMAIN", "").lower().strip()
    email = (email or "").lower().strip()

    # Retorna True se existir domínio configurado e o email terminar com ele
    return bool(domain) and email.endswith(f"@{domain}")


def user_can_manage_landing_content(user):
    """
    Verifica se o usuário pode editar conteúdo público (landing page).
    """
    # Usuário precisa estar autenticado
    if not getattr(user, "is_authenticated", False):
        return False

    # Admin sempre pode
    if user.is_staff:
        return True

    # Verifica permissão no perfil
    profile = getattr(user, "profile", None)
    return bool(profile and profile.can_manage_landing_page)


class Profile(models.Model):
    """
    Perfil complementar do usuário com papéis e permissões do sistema.
    """

    # Relação 1-para-1 com o usuário
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",  # permite acessar user.profile
    )

    # Nome exibido no sistema
    display_name = models.CharField("nome de exibicao", max_length=150, blank=True)

    # Matrícula institucional (SIAPE, RA, etc.)
    institutional_id = models.CharField("matricula ou SIAPE", max_length=30, blank=True)

    # Flags de papéis do usuário
    is_student = models.BooleanField("aluno", default=False)
    is_professor = models.BooleanField("professor", default=False)
    is_technician = models.BooleanField("tecnico administrativo", default=False)
    is_department_head = models.BooleanField("chefe de departamento", default=False)
    is_course_coordinator = models.BooleanField("coordenador de curso", default=False)
    is_internship_coordinator = models.BooleanField("coordenador de estagio", default=False)
    is_tcc1_coordinator = models.BooleanField("coordenador de TCC 1", default=False)
    is_tcc2_coordinator = models.BooleanField("coordenador de TCC 2", default=False)

    # Permissão específica
    can_manage_landing_page = models.BooleanField(
        "pode gerenciar landing page",
        default=False,
    )

    # Datas automáticas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfis"

    def __str__(self):
        # Define como o objeto será exibido no admin
        return self.display_name or self.user.get_full_name() or self.user.email

    def clean(self):
        """
        Validação antes de salvar no banco.
        Garante que o email do usuário seja institucional.
        """
        if self.user.email and not is_institutional_email(self.user.email):
            raise ValidationError(
                {"user": "Utilize apenas e-mails institucionais do departamento."}
            )

    @property
    def role_labels(self):
        """
        Retorna lista legível dos papéis ativos do usuário.
        Ex: ["Aluno", "Professor"]
        """
        labels = []

        options = [
            (self.is_student, "Aluno"),
            (self.is_professor, "Professor"),
            (self.is_technician, "Tecnico administrativo"),
            (self.is_department_head, "Chefe de departamento"),
            (self.is_course_coordinator, "Coordenador de curso"),
            (self.is_internship_coordinator, "Coordenador de estagio"),
            (self.is_tcc1_coordinator, "Coordenador de TCC 1"),
            (self.is_tcc2_coordinator, "Coordenador de TCC 2"),
        ]

        # Adiciona apenas os papéis ativos
        for enabled, label in options:
            if enabled:
                labels.append(label)

        return labels


class AccessInvitation(models.Model):
    """
    Convite de acesso para novos usuários entrarem no sistema.
    """

    # Email convidado (único)
    email = models.EmailField(unique=True)

    # Token único usado no link de convite
    token = models.CharField(max_length=80, unique=True, editable=False)

    # Observações opcionais
    notes = models.TextField("observacoes", blank=True)

    # Quem enviou o convite
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_access_invitations",
    )

    # Usuário que aceitou o convite
    accepted_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accepted_access_invitations",
    )

    # Controle de datas
    sent_at = models.DateTimeField("enviado em", null=True, blank=True)
    accepted_at = models.DateTimeField("aceito em", null=True, blank=True)
    expires_at = models.DateTimeField("expira em")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "convite de acesso"
        verbose_name_plural = "convites de acesso"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @classmethod
    def find_by_token(cls, raw_token):
        """
        Busca convite pelo token, tolerando variações (links quebrados).
        """
        token = (raw_token or "").strip()
        if not token:
            return None

        # Busca direta
        direct_match = cls.objects.filter(token=token).first()
        if direct_match:
            return direct_match

        # Normaliza token
        normalized = token.replace("+", "-").replace("/", "_").rstrip("=")
        if normalized != token:
            match = cls.objects.filter(token=normalized).first()
            if match:
                return match

        # Busca por prefixo (caso truncado)
        if len(normalized) >= 32:
            matches = list(cls.objects.filter(token__startswith=normalized)[:2])
            if len(matches) == 1:
                return matches[0]

        return None

    def clean(self):
        """
        Validação do email institucional.
        """
        self.email = (self.email or "").strip().lower()
        if not is_institutional_email(self.email):
            raise ValidationError(
                {"email": "Utilize apenas e-mails institucionais do departamento."}
            )

    def save(self, *args, **kwargs):
        """
        Sobrescreve save para gerar token e definir expiração automaticamente.
        """
        self.email = (self.email or "").strip().lower()

        # Gera token se não existir
        if not self.token:
            self.token = secrets.token_urlsafe(32)

        # Define expiração padrão
        if not self.expires_at:
            days = getattr(settings, "INVITATION_TTL_DAYS", 7)
            self.expires_at = timezone.now() + timedelta(days=days)

        # Valida antes de salvar
        self.full_clean()

        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Verifica se o convite expirou."""
        return timezone.now() >= self.expires_at

    @property
    def is_usable(self):
        """Verifica se ainda pode ser usado."""
        return self.accepted_at is None and not self.is_expired

    def mark_as_accepted(self, user):
        """Marca convite como aceito."""
        self.accepted_user = user
        self.accepted_at = timezone.now()
        self.save(update_fields=["accepted_user", "accepted_at", "updated_at"])


    def build_acceptance_url(self, request=None):
        """
        Monta o link do convite que leva para a view accept_invitation.
        Essa view já integra com o fluxo do allauth.
        """
        path = reverse("accounts:accept_invitation", args=[self.token])

        if request is not None:
            return request.build_absolute_uri(path)

        base_url = getattr(settings, "SITE_BASE_URL", "").rstrip("/")
        return f"{base_url}{path}"


    def send_invitation_email(self, request=None):
        """
        Envia o convite de primeiro acesso.
        O usuário clica no link, cai em accept_invitation,
        e dali segue para o login social institucional.
        """
        acceptance_url = self.build_acceptance_url(request)

        send_mail(
            subject="Convite de acesso ao portal DECOM",
            message=(
                f"Olá,\n\n"
                f"Você recebeu um convite para acessar o portal DECOM.\n\n"
                f"Use o link abaixo para iniciar seu primeiro acesso:\n\n"
                f"{acceptance_url}\n\n"
                f"Após abrir o link, entre com sua conta institucional.\n\n"
                f"Esse convite expira em {self.expires_at:%d/%m/%Y às %H:%M}."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.email],
            fail_silently=False,
        )

        type(self).objects.filter(pk=self.pk).update(
            sent_at=timezone.now(),
            updated_at=timezone.now(),
        )
        self.sent_at = timezone.now()


class LoginCode(models.Model):
    """
    Código temporário (OTP) para login sem senha.
    """

    # Usuário relacionado
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="login_codes",
    )

    # Email usado para envio
    delivery_email = models.EmailField()

    # Código armazenado com hash (segurança)
    code_hash = models.CharField(max_length=128)

    # Número de tentativas
    attempts = models.PositiveSmallIntegerField(default=0)

    # Datas
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    # Marca quando foi usado
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "codigo de acesso"
        verbose_name_plural = "codigos de acesso"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} ({self.created_at:%d/%m/%Y %H:%M})"

    @classmethod
    def issue_for_user(cls, user):
        """
        Gera um novo código OTP e invalida os anteriores.
        """
        now = timezone.now()
        ttl_minutes = getattr(settings, "LOGIN_CODE_TTL_MINUTES", 10)

        # Remove códigos ativos antigos
        cls.objects.filter(
            user=user,
            consumed_at__isnull=True,
            expires_at__gt=now,
        ).delete()

        # Gera código de 6 dígitos
        raw_code = f"{secrets.randbelow(1_000_000):06d}"

        # Salva com hash
        code = cls.objects.create(
            user=user,
            delivery_email=user.email,
            code_hash=make_password(raw_code),
            expires_at=now + timedelta(minutes=ttl_minutes),
        )

        return code, raw_code

    def verify(self, raw_code):
        """
        Verifica se o código informado é válido.
        """
        max_attempts = getattr(settings, "LOGIN_CODE_MAX_ATTEMPTS", 5)

        # Bloqueia se expirado, usado ou excedeu tentativas
        if self.consumed_at or self.expires_at <= timezone.now() or self.attempts >= max_attempts:
            return False

        return check_password(raw_code, self.code_hash)

    def register_failure(self):
        """Incrementa tentativas."""
        self.attempts = models.F("attempts") + 1
        self.save(update_fields=["attempts"])
        self.refresh_from_db(fields=["attempts"])

    def mark_as_used(self):
        """Marca código como utilizado."""
        self.consumed_at = timezone.now()
        self.save(update_fields=["consumed_at"])