from importlib.util import find_spec
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware

from .adapters import InstitutionalSocialAccountAdapter
from .invitations import PENDING_INVITATION_SESSION_KEY
from .models import AccessInvitation, LoginCode, Profile


User = get_user_model()
ALLAUTH_AVAILABLE = find_spec("allauth") is not None


@override_settings(ENABLE_ALLAUTH_LOGIN=False, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="vivas",
            email="vivas@ufvjm.edu.br",
            first_name="Vivas",
        )
        self.user.set_unusable_password()
        self.user.save()

    def test_request_code_sends_email(self):
        response = self.client.post(
            reverse("accounts:login_request"),
            {"email": "vivas@ufvjm.edu.br"},
        )

        self.assertRedirects(response, reverse("accounts:verify_login_code"))
        self.assertEqual(LoginCode.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_verify_code_logs_user_in(self):
        login_code, raw_code = LoginCode.issue_for_user(self.user)
        session = self.client.session
        session["accounts_pending_login_user_id"] = self.user.pk
        session.save()

        response = self.client.post(
            reverse("accounts:verify_login_code"),
            {"code": raw_code},
        )

        self.assertRedirects(response, reverse("accounts:dashboard"))
        self.assertEqual(str(self.client.session.get("_auth_user_id")), str(self.user.pk))
        login_code.refresh_from_db()
        self.assertIsNotNone(login_code.consumed_at)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class InvitationFlowTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username="admin-local",
            email="admin@ufvjm.edu.br",
            is_staff=True,
        )
        self.admin_user.set_unusable_password()
        self.admin_user.save()
        self.invitation = AccessInvitation.objects.create(
            email="convidado@ufvjm.edu.br",
            invited_by=self.admin_user,
        )
        self.professors_group = Group.objects.get(name="Professores")
        self.course_coordinators_group = Group.objects.get(name="Coordenadores de curso")
        self.students_group = Group.objects.get(name="Alunos")
        self.landing_editors_group = Group.objects.get(name="Editores da landing page")

    def test_accept_invitation_stashes_token_in_session(self):
        response = self.client.get(
            reverse("accounts:accept_invitation", kwargs={"token": self.invitation.token})
        )

        self.assertEqual(
            self.client.session.get(PENDING_INVITATION_SESSION_KEY),
            self.invitation.token,
        )
        if settings.ENABLE_ALLAUTH_LOGIN:
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse("google_login"))
        else:
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, self.invitation.email)

    def test_send_invitation_email_outputs_link(self):
        self.invitation.send_invitation_email()
        self.invitation.refresh_from_db()

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.invitation.token, mail.outbox[0].body)
        self.assertIsNotNone(self.invitation.sent_at)

    def test_accept_invitation_renders_expired_state_when_needed(self):
        self.invitation.expires_at = self.invitation.created_at
        self.invitation.save(update_fields=["expires_at"])

        response = self.client.get(
            reverse("accounts:accept_invitation", kwargs={"token": self.invitation.token})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Este link expirou")

    def test_staff_panel_creates_invitation_and_sends_email(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("accounts:invitation_panel"),
            {
                "email": "novo-admin@ufvjm.edu.br",
                "notes": "Convite pela interface do portal",
                "groups": [self.professors_group.id],
            },
        )

        self.assertRedirects(response, reverse("accounts:invitation_panel"))
        invitation = AccessInvitation.objects.get(email="novo-admin@ufvjm.edu.br")
        self.assertEqual(invitation.invited_by, self.admin_user)
        self.assertTrue(invitation.groups.filter(name="Professores").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(invitation.token, mail.outbox[0].body)

    def test_accepting_invitation_applies_roles_to_profile(self):
        user = User.objects.create_user(
            username="docente",
            email=self.invitation.email,
            is_active=True,
        )
        user.set_unusable_password()
        user.save()
        self.invitation.groups.set([self.professors_group, self.course_coordinators_group])
        self.client.force_login(user)

        response = self.client.get(
            reverse("accounts:accept_invitation", kwargs={"token": self.invitation.token})
        )

        self.assertRedirects(response, reverse("accounts:dashboard"))
        user.profile.refresh_from_db()
        self.assertTrue(user.groups.filter(name="Professores").exists())
        self.assertTrue(user.groups.filter(name="Coordenadores de curso").exists())

    def test_non_staff_cannot_access_staff_panel(self):
        user = User.objects.create_user(
            username="aluno",
            email="aluno@ufvjm.edu.br",
            is_staff=False,
        )
        user.set_unusable_password()
        user.save()
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:invitation_panel"))

        self.assertEqual(response.status_code, 403)

    def test_staff_can_resend_invitation_from_site_panel(self):
        self.client.force_login(self.admin_user)
        original_token = self.invitation.token

        response = self.client.post(
            reverse("accounts:resend_invitation", args=[self.invitation.id]),
        )

        self.assertRedirects(response, reverse("accounts:invitation_panel"))
        self.assertEqual(len(mail.outbox), 1)
        self.invitation.refresh_from_db()
        self.assertNotEqual(self.invitation.token, original_token)
        self.assertIn(self.invitation.token, mail.outbox[0].body)
        self.assertNotIn(original_token, mail.outbox[0].body)
        self.assertIsNotNone(self.invitation.sent_at)

    def test_superuser_can_update_registered_person_profile(self):
        self.admin_user.is_superuser = True
        self.admin_user.save(update_fields=["is_superuser"])
        person = User.objects.create_user(
            username="pessoa",
            email="pessoa@ufvjm.edu.br",
            is_active=True,
        )
        person.set_unusable_password()
        person.save()
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("accounts:invitation_panel"),
            {
                "action": "update_profile",
                "user_id": person.id,
                f"profile_{person.id}-display_name": "Pessoa Teste",
                f"profile_{person.id}-institutional_id": "SIAPE-123",
                f"profile_{person.id}-groups": [
                    self.students_group.id,
                    self.landing_editors_group.id,
                ],
            },
        )

        self.assertRedirects(response, reverse("accounts:invitation_panel"))
        person.profile.refresh_from_db()
        self.assertEqual(person.profile.display_name, "Pessoa Teste")
        self.assertEqual(person.profile.institutional_id, "SIAPE-123")
        self.assertTrue(person.groups.filter(name="Alunos").exists())
        self.assertTrue(person.groups.filter(name="Editores da landing page").exists())

    def test_staff_panel_consolidates_user_and_invitation_by_email(self):
        person = User.objects.create_user(
            username="duplicado",
            email="duplicado@ufvjm.edu.br",
            is_active=True,
        )
        person.set_unusable_password()
        person.save()
        profile, _ = Profile.objects.get_or_create(user=person)
        profile.display_name = "Pessoa Consolidada"
        profile.save(update_fields=["display_name"])
        AccessInvitation.objects.create(
            email=person.email,
            invited_by=self.admin_user,
        )
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("accounts:invitation_panel"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "duplicado@ufvjm.edu.br", count=1)

    def test_staff_panel_displays_group_labels_in_singular(self):
        person = User.objects.create_user(
            username="rotulo",
            email="rotulo@ufvjm.edu.br",
            is_active=True,
        )
        person.set_unusable_password()
        person.save()
        person.groups.add(self.students_group, self.professors_group)
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse("accounts:invitation_panel"),
            {"q": person.email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aluno")
        self.assertContains(response, "Professor")
        self.assertNotContains(response, "Alunos")
        self.assertNotContains(response, "Professores")

    def test_staff_panel_hides_link_actions_for_accepted_invitation(self):
        person = User.objects.create_user(
            username="aceito",
            email="aceito@ufvjm.edu.br",
            is_active=True,
        )
        person.set_unusable_password()
        person.save()
        invitation = AccessInvitation.objects.create(
            email=person.email,
            invited_by=self.admin_user,
        )
        invitation.mark_as_accepted(person)
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse("accounts:invitation_panel"),
            {"q": person.email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Primeiro acesso")
        self.assertContains(response, "Aceito")
        self.assertNotContains(response, "Abrir link")
        self.assertNotContains(response, "Reenviar Link")
        self.assertNotContains(response, "Renovar Link")
        self.assertNotContains(response, "Validade:")
        self.assertNotContains(response, "Ultimo envio:")

    def test_staff_without_superuser_cannot_update_registered_person_profile(self):
        person = User.objects.create_user(
            username="sem-permissao",
            email="sem-permissao@ufvjm.edu.br",
            is_active=True,
        )
        person.set_unusable_password()
        person.save()
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse("accounts:invitation_panel"),
            {
                "action": "update_profile",
                "user_id": person.id,
                "display_name": "Alterado",
                "groups": [self.professors_group.id],
            },
        )

        self.assertEqual(response.status_code, 403)
        person.profile.refresh_from_db()
        self.assertNotEqual(person.profile.display_name, "Alterado")

    def test_accept_invitation_accepts_high_entropy_prefix_token(self):
        truncated_token = f"{self.invitation.token[:37]}="

        response = self.client.get(
            reverse("accounts:accept_invitation", kwargs={"token": truncated_token})
        )

        self.assertEqual(
            self.client.session.get(PENDING_INVITATION_SESSION_KEY),
            self.invitation.token,
        )
        if settings.ENABLE_ALLAUTH_LOGIN:
            self.assertEqual(response.status_code, 302)
        else:
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, self.invitation.email)

    def test_invalid_invitation_renders_friendly_404_page(self):
        response = self.client.get(
            reverse("accounts:accept_invitation", kwargs={"token": "convite-invalido"})
        )

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "nao corresponde a uma autorizacao valida", status_code=404)

    def test_renew_keeps_same_token(self):
        original_token = self.invitation.token

        self.invitation.renew()
        self.invitation.refresh_from_db()

        self.assertEqual(self.invitation.token, original_token)

    def test_admin_access_invitation_changelist_loads(self):
        self.admin_user.is_superuser = True
        self.admin_user.save(update_fields=["is_superuser"])
        self.client.force_login(self.admin_user)

        response = self.client.get("/admin/accounts/accessinvitation/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.invitation.email)


class LoginPageRenderingTests(TestCase):
    def test_login_page_has_explicit_input_styling(self):
        response = self.client.get(reverse("accounts:login_request"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login")
        self.assertContains(response, "Entrar no portal")
        self.assertContains(response, "primeiro cadastro")
        if settings.ENABLE_ALLAUTH_LOGIN:
            self.assertContains(response, "conta institucional")
        else:
            self.assertContains(response, "Receber codigo de acesso")

    def test_staff_navigation_exposes_invitation_panel_link(self):
        user = User.objects.create_user(
            username="gestor",
            email="gestor@ufvjm.edu.br",
            is_staff=True,
        )
        user.set_unusable_password()
        user.save()
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:dashboard"))

        self.assertContains(response, reverse("accounts:invitation_panel"))

    def test_content_manager_sees_landing_editor_link_on_dashboard(self):
        user = User.objects.create_user(
            username="front",
            email="front@ufvjm.edu.br",
            is_staff=False,
        )
        user.set_unusable_password()
        user.save()
        user.groups.add(Group.objects.get(name="Editores da landing page"))
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:dashboard"))

        self.assertContains(response, reverse("home:landing_editor"))


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class InstitutionalSocialAccountAdapterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.adapter = InstitutionalSocialAccountAdapter()
        self.existing_user = User.objects.create_user(
            username="vivas",
            email="vivas@ufvjm.edu.br",
            first_name="Vivas",
            is_active=True,
        )
        self.existing_user.set_unusable_password()
        self.existing_user.save()

    def _build_request(self):
        request = self.factory.get("/")
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        setattr(request, "_messages", FallbackStorage(request))
        return request

    def _build_sociallogin(self, email, hd="", email_verified=True, address_verified=True):
        if not ALLAUTH_AVAILABLE:
            self.skipTest("allauth nao esta instalado neste ambiente")

        from allauth.account.models import EmailAddress

        extra_data = {"email": email, "email_verified": email_verified}
        if hd:
            extra_data["hd"] = hd

        return SimpleNamespace(
            user=SimpleNamespace(email=email),
            account=SimpleNamespace(extra_data=extra_data),
            email_addresses=[
                EmailAddress(email=email, verified=address_verified, primary=True)
            ],
        )

    def test_allows_existing_active_user(self):
        request = self._build_request()
        sociallogin = self._build_sociallogin(
            email="vivas@ufvjm.edu.br",
            hd="ufvjm.edu.br",
        )

        self.adapter.pre_social_login(request, sociallogin)

    def test_allows_new_user_only_with_pending_invitation(self):
        request = self._build_request()
        invitation = AccessInvitation.objects.create(email="novo@ufvjm.edu.br")
        request.session[PENDING_INVITATION_SESSION_KEY] = invitation.token
        request.session.save()
        sociallogin = self._build_sociallogin(
            email="novo@ufvjm.edu.br",
            hd="ufvjm.edu.br",
        )

        self.adapter.pre_social_login(request, sociallogin)
        self.assertTrue(self.adapter.is_open_for_signup(request, sociallogin))

    def test_rejects_non_invited_institutional_email(self):
        request = self._build_request()
        sociallogin = self._build_sociallogin(
            email="naoautorizado@ufvjm.edu.br",
            hd="ufvjm.edu.br",
        )

        from allauth.core.exceptions import ImmediateHttpResponse

        with self.assertRaises(ImmediateHttpResponse) as ctx:
            self.adapter.pre_social_login(request, sociallogin)

        response = ctx.exception.response
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:login_request"))
        self.assertEqual(
            [str(message) for message in get_messages(request)],
            ["Seu e-mail institucional ainda nao foi autorizado. Solicite a liberacao a um administrador do sistema."],
        )
