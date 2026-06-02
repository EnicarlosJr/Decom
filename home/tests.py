from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .models import LandingPageContent


User = get_user_model()


class HomeViewTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("home:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Departamento de Computacao")

    def test_default_landing_starts_without_sample_public_content(self):
        page = LandingPageContent.get_solo()

        self.assertEqual(page.hero_title, "")
        self.assertFalse(page.items.exists())

        response = self.client.get(reverse("home:index"))

        self.assertNotContains(response, "Primeiro acesso por convite")
        self.assertNotContains(response, "Nenhum card principal foi publicado ainda")

    def test_home_page_uses_saved_landing_content(self):
        page = LandingPageContent.get_solo()
        page.hero_title = "Portal customizado para os usuarios"
        page.save(update_fields=["hero_title", "updated_at"])

        response = self.client.get(reverse("home:index"))

        self.assertContains(response, "Portal customizado para os usuarios")

    def test_landing_editor_requires_authorized_user(self):
        user = User.objects.create_user(
            username="visitante",
            email="visitante@ufvjm.edu.br",
        )
        user.set_unusable_password()
        user.save()
        self.client.force_login(user)

        response = self.client.get(reverse("home:landing_editor"))

        self.assertEqual(response.status_code, 403)

    def test_landing_editor_is_available_for_front_manager(self):
        user = User.objects.create_user(
            username="conteudo",
            email="conteudo@ufvjm.edu.br",
        )
        user.set_unusable_password()
        user.save()
        user.groups.add(Group.objects.get(name="Editores da landing page"))
        self.client.force_login(user)

        response = self.client.get(reverse("home:landing_editor"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar landing page")
