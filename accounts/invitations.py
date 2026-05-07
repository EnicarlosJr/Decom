"""Utilitarios de sessao para gerenciar convites pendentes no navegador."""

from .models import AccessInvitation


PENDING_INVITATION_SESSION_KEY = "accounts_pending_invitation_token"


def clear_pending_invitation(request):
    """Remove o token de convite atualmente guardado na sessao."""
    request.session.pop(PENDING_INVITATION_SESSION_KEY, None)


def set_pending_invitation(request, invitation):
    """Associa o token do convite atual a sessao do navegador."""
    request.session[PENDING_INVITATION_SESSION_KEY] = invitation.token


def get_pending_invitation(request):
    """Recupera o convite salvo em sessao, limpando referencias invalidas."""
    token = request.session.get(PENDING_INVITATION_SESSION_KEY)
    if not token:
        return None
    invitation = AccessInvitation.objects.filter(token=token).first()
    if invitation is None:
        clear_pending_invitation(request)
        return None
    return invitation


def get_valid_pending_invitation(request, email=None):
    """Retorna o convite em sessao apenas se ele ainda estiver utilizavel."""
    invitation = get_pending_invitation(request)
    if invitation is None:
        return None
    if not invitation.is_usable:
        clear_pending_invitation(request)
        return None
    if email and invitation.email.lower() != email.lower():
        return None
    return invitation
