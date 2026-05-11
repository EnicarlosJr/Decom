from django.conf import settings
from django.core.mail import send_mail


def send_invitation_email(invitation):
    link = f"{settings.SITE_BASE_URL}/accounts/convite/{invitation.token}/"

    send_mail(
        subject="Convite de acesso ao portal DECOM",
        message=(
            f"Olá,\n\n"
            f"Acesse o sistema usando este link:\n\n"
            f"{link}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.email],
        fail_silently=False,
    )