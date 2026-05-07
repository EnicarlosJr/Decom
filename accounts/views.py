"""Views do fluxo de autenticacao, painel e gestao de convites.

Este modulo concentra a experiencia do usuario no portal:
- entrada por login social ou codigo
- validacao do primeiro acesso por convite
- painel autenticado
- operacao de convites pela equipe administrativa
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from .invitations import clear_pending_invitation, get_valid_pending_invitation, set_pending_invitation
from .forms import AccessInvitationSiteForm, RequestLoginCodeForm, VerifyLoginCodeForm
from .models import AccessInvitation, LoginCode, user_can_manage_landing_content


User = get_user_model()

PENDING_USER_SESSION_KEY = "accounts_pending_login_user_id"
PENDING_NEXT_SESSION_KEY = "accounts_pending_login_next_url"


def _clear_pending_login(request):
    """Remove qualquer estado temporario de autenticacao pendente."""
    request.session.pop(PENDING_USER_SESSION_KEY, None)
    request.session.pop(PENDING_NEXT_SESSION_KEY, None)
    clear_pending_invitation(request)


def _get_social_login_url():
    """Resolve a rota do login social, quando o allauth estiver habilitado."""
    if not getattr(settings, "ENABLE_ALLAUTH_LOGIN", False):
        return None
    try:
        return reverse("google_login")
    except NoReverseMatch:
        return None


def _ensure_staff_user(request):
    """Garante que apenas usuarios staff acessem a gestao de convites."""
    if not request.user.is_authenticated:
        return redirect("accounts:login_request")
    if not request.user.is_staff:
        raise PermissionDenied
    return None


def _build_invitation_rows(request, invitations):
    """Prepara URLs absolutas para a listagem de convites na interface."""
    rows = []
    for invitation in invitations:
        rows.append(
            {
                "obj": invitation,
                "acceptance_url": invitation.build_acceptance_url(request),
            }
        )
    return rows


def _build_access_modules(user, profile):
    """Define os blocos operacionais exibidos no painel do usuario."""
    modules = [
        {
            "title": "Minha conta",
            "description": "Dados pessoais, acesso atual e informacoes basicas do usuario.",
            "status": "Disponivel",
            "tone": "ready",
        },
    ]

    if user.is_staff:
        modules.append(
            {
                "title": "Convites",
                "description": "Criar, reenviar e acompanhar liberacoes de acesso.",
                "status": "Admin",
                "tone": "restricted",
            }
        )

    if user_can_manage_landing_content(user):
        modules.append(
            {
                "title": "Landing page",
                "description": "Editar a capa publica do portal sem alterar o layout.",
                "status": "Editor",
                "tone": "restricted",
            }
        )

    return modules


def request_login_code(request):
    """Exibe a tela unica de login e inicia o fluxo por codigo quando necessario."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    next_url = request.GET.get("next") or request.session.get(PENDING_NEXT_SESSION_KEY) or ""
    social_login_url = _get_social_login_url()
    login_mode = "social" if getattr(settings, "ENABLE_ALLAUTH_LOGIN", False) else "code"

    if request.method == "POST" and login_mode == "code":
        form = RequestLoginCodeForm(request.POST)
        next_url = request.POST.get("next", "").strip()
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.filter(email__iexact=email, is_active=True).first()

            if user is None:
                messages.error(
                    request,
                    "Nao encontramos um usuario ativo com este e-mail. Solicite o cadastro ao departamento.",
                )
            else:
                login_code, raw_code = LoginCode.issue_for_user(user)
                request.session[PENDING_USER_SESSION_KEY] = user.pk
                request.session[PENDING_NEXT_SESSION_KEY] = next_url

                send_mail(
                    subject="Codigo de acesso ao portal DECOM",
                    message=(
                        "Seu codigo de acesso ao portal do DECOM e "
                        f"{raw_code}. Ele expira em "
                        f"{getattr(settings, 'LOGIN_CODE_TTL_MINUTES', 10)} minutos."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                )

                messages.success(
                    request,
                    f"Enviamos um codigo para {login_code.delivery_email}.",
                )
                return redirect("accounts:verify_login_code")
    else:
        form = RequestLoginCodeForm()

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "login_mode": login_mode,
            "next_url": next_url,
            "social_login_url": social_login_url,
            "pending_invitation": get_valid_pending_invitation(request),
        },
    )


def accept_invitation(request, token):
    """Valida o convite de primeiro acesso e encaminha para autenticacao."""
    invitation = AccessInvitation.find_by_token(token)
    social_login_url = _get_social_login_url()

    if invitation is None:
        clear_pending_invitation(request)
        return render(
            request,
            "accounts/accept_invitation.html",
            {
                "invitation": None,
                "social_login_url": social_login_url,
                "invitation_status": "invalid",
            },
            status=404,
        )

    if request.user.is_authenticated:
        if request.user.email.lower() == invitation.email.lower():
            if invitation.accepted_at is None:
                invitation.mark_as_accepted(request.user)
            clear_pending_invitation(request)
            messages.success(request, "Convite validado com sucesso.")
            return redirect("accounts:dashboard")
        messages.error(
            request,
            f"Voce esta autenticado com {request.user.email}. Saia e entre com {invitation.email}.",
        )

    if invitation.accepted_at is not None:
        return render(
            request,
            "accounts/accept_invitation.html",
            {
                "invitation": invitation,
                "social_login_url": social_login_url,
                "invitation_status": "accepted",
            },
        )

    if invitation.is_expired:
        clear_pending_invitation(request)
        return render(
            request,
            "accounts/accept_invitation.html",
            {
                "invitation": invitation,
                "social_login_url": social_login_url,
                "invitation_status": "expired",
            },
        )

    set_pending_invitation(request, invitation)
    if social_login_url:
        return redirect(social_login_url)
    return render(
        request,
        "accounts/accept_invitation.html",
        {
            "invitation": invitation,
            "social_login_url": social_login_url,
            "invitation_status": "ready",
        },
    )


def verify_login_code(request):
    """Confirma o codigo temporario enviado por e-mail."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    pending_user_id = request.session.get(PENDING_USER_SESSION_KEY)
    if not pending_user_id:
        messages.info(request, "Informe seu e-mail institucional para receber um codigo.")
        return redirect("accounts:login_request")

    user = User.objects.filter(pk=pending_user_id, is_active=True).first()
    if user is None:
        _clear_pending_login(request)
        messages.error(request, "Seu acesso pendente expirou. Solicite um novo codigo.")
        return redirect("accounts:login_request")

    active_code = LoginCode.get_active_for_user(user)
    if active_code is None:
        _clear_pending_login(request)
        messages.error(request, "O codigo expirou. Solicite um novo acesso.")
        return redirect("accounts:login_request")

    if request.method == "POST":
        form = VerifyLoginCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            if active_code.verify(code):
                active_code.mark_as_used()
                login(
                    request,
                    user,
                    backend="django.contrib.auth.backends.ModelBackend",
                )
                next_url = request.session.get(PENDING_NEXT_SESSION_KEY) or reverse(
                    "accounts:dashboard"
                )
                _clear_pending_login(request)
                messages.success(request, "Autenticacao concluida com sucesso.")
                return redirect(next_url)

            active_code.register_failure()
            messages.error(
                request,
                "Codigo invalido. Confira o e-mail recebido e tente novamente.",
            )
    else:
        form = VerifyLoginCodeForm()

    return render(
        request,
        "accounts/verify_login_code.html",
        {
            "form": form,
            "pending_email": user.email,
            "expires_at": active_code.expires_at,
            "remaining_attempts": active_code.remaining_attempts,
        },
    )


@login_required
def dashboard(request):
    """Renderiza o painel autenticado do usuario."""
    profile = getattr(request.user, "profile", None)
    role_labels = profile.role_labels if profile else []
    access_modules = _build_access_modules(request.user, profile)
    can_manage_landing_page = user_can_manage_landing_content(request.user)
    invitation_metrics = None
    if request.user.is_staff:
        invitations = AccessInvitation.objects.all()
        invitation_metrics = {
            "total": invitations.count(),
            "pending": sum(1 for invitation in invitations if invitation.is_usable),
            "accepted": invitations.filter(accepted_at__isnull=False).count(),
            "expired": sum(1 for invitation in invitations if invitation.is_expired and invitation.accepted_at is None),
        }
    return render(
        request,
        "accounts/dashboard.html",
        {
            "profile": profile,
            "role_labels": role_labels,
            "access_modules": access_modules,
            "can_manage_landing_page": can_manage_landing_page,
            "invitation_metrics": invitation_metrics,
        },
    )


def invitation_panel(request):
    """Tela operacional para criar, filtrar e reenviar convites."""
    access_check = _ensure_staff_user(request)
    if access_check is not None:
        return access_check

    now = timezone.now()

    if request.method == "POST":
        form = AccessInvitationSiteForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            notes = form.cleaned_data["notes"].strip()
            invitation = AccessInvitation.objects.filter(email__iexact=email).first()

            if invitation and invitation.accepted_at is not None:
                messages.error(
                    request,
                    "Este e-mail ja concluiu o cadastro e ja possui acesso autorizado.",
                )
            else:
                created = invitation is None
                if created:
                    invitation = AccessInvitation(
                        email=email,
                        notes=notes,
                        invited_by=request.user,
                    )
                    invitation.save()
                else:
                    if invitation.is_expired:
                        invitation.renew()
                    invitation.notes = notes
                    invitation.invited_by = request.user
                    invitation.save(update_fields=["notes", "invited_by", "updated_at"])

                invitation.send_invitation_email(request)
                messages.success(
                    request,
                    f"Convite {'enviado' if created else 'reenviado'} para {invitation.email}.",
                )
                return redirect("accounts:invitation_panel")
    else:
        form = AccessInvitationSiteForm()

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "all").strip() or "all"

    base_queryset = AccessInvitation.objects.select_related("invited_by", "accepted_user")
    filtered_queryset = base_queryset
    if query:
        filtered_queryset = filtered_queryset.filter(email__icontains=query)
    if status == "pending":
        filtered_queryset = filtered_queryset.filter(accepted_at__isnull=True, expires_at__gt=now)
    elif status == "accepted":
        filtered_queryset = filtered_queryset.filter(accepted_at__isnull=False)
    elif status == "expired":
        filtered_queryset = filtered_queryset.filter(accepted_at__isnull=True, expires_at__lte=now)

    invitations = list(base_queryset)
    metrics = {
        "total": len(invitations),
        "pending": sum(1 for invitation in invitations if invitation.is_usable),
        "accepted": sum(1 for invitation in invitations if invitation.accepted_at is not None),
        "expired": sum(1 for invitation in invitations if invitation.is_expired and invitation.accepted_at is None),
    }
    return render(
        request,
        "accounts/invitation_panel.html",
        {
            "form": form,
            "metrics": metrics,
            "social_login_url": _get_social_login_url(),
            "invitation_rows": _build_invitation_rows(request, list(filtered_queryset)),
            "filters": {
                "query": query,
                "status": status,
            },
        },
    )


def resend_invitation(request, invitation_id):
    """Reenvia ou renova um convite existente a partir do painel."""
    access_check = _ensure_staff_user(request)
    if access_check is not None:
        return access_check
    if request.method != "POST":
        raise PermissionDenied

    invitation = get_object_or_404(AccessInvitation, pk=invitation_id)
    if invitation.accepted_at is not None:
        messages.error(
            request,
            "Este convite ja foi aceito e nao precisa de reenvio.",
        )
        return redirect("accounts:invitation_panel")

    if invitation.is_expired:
        invitation.renew()
    invitation.invited_by = request.user
    invitation.save(update_fields=["invited_by", "updated_at"])
    invitation.send_invitation_email(request)
    messages.success(request, f"Convite reenviado para {invitation.email}.")
    return redirect("accounts:invitation_panel")


def logout_view(request):
    """Encerra a sessao atual e limpa estados temporarios de login."""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Sua sessao foi encerrada.")
    _clear_pending_login(request)
    return redirect("home:index")
