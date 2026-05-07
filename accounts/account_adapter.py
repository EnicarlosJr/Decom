"""Adaptador de conta local para impedir cadastro publico espontaneo."""

from allauth.account.adapter import DefaultAccountAdapter


class DepartmentAccountAdapter(DefaultAccountAdapter):
    """Mantem o cadastro fechado fora do fluxo controlado por convite."""

    def is_open_for_signup(self, request):
        return False
