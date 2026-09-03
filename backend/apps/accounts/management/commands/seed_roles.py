"""Seed dos papéis e permissões (doc 04). Idempotente.

Uso: python manage.py seed_roles
"""
from django.core.management.base import BaseCommand

from apps.accounts.models import Permission, Role
from apps.accounts.rbac import PERMISSION_CATALOG, ROLE_PERMISSIONS, ROLES


class Command(BaseCommand):
    help = "Cria/atualiza os 5 papéis e o catálogo de permissões (doc 04)."

    def handle(self, *args, **options):
        perms = {}
        for code, name, module in PERMISSION_CATALOG:
            perm, _ = Permission.objects.get_or_create(
                code=code, defaults={"name": name, "module": module}
            )
            perms[code] = perm
        roles = {}
        for code, name in ROLES:
            role, _ = Role.objects.get_or_create(code=code, defaults={"name": name})
            role.permissions.set(perms[c] for c in ROLE_PERMISSIONS.get(code, ()))
            roles[code] = role
        self.stdout.write(
            self.style.SUCCESS(
                f"seed_roles OK: {len(perms)} permissões, {len(roles)} papéis."
            )
        )
