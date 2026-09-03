from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class Permission(models.Model):
    """Permissão do domínio (doc 06 — Permission)."""

    code = models.CharField(max_length=64, unique=True, verbose_name="código")
    name = models.CharField(max_length=120, verbose_name="nome")
    module = models.CharField(max_length=64, blank=True, verbose_name="módulo")

    class Meta:
        ordering = ["code"]
        verbose_name = "permissão"
        verbose_name_plural = "permissões"

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class Role(models.Model):
    """Papel do domínio (doc 06 — Role): um dos 5 perfis do doc 04."""

    code = models.CharField(max_length=32, unique=True, verbose_name="código")
    name = models.CharField(max_length=80, verbose_name="nome")
    permissions = models.ManyToManyField(
        Permission, related_name="roles", blank=True, verbose_name="permissões"
    )

    class Meta:
        ordering = ["code"]
        verbose_name = "papel"
        verbose_name_plural = "papéis"

    def __str__(self) -> str:
        return self.name


class UserManager(BaseUserManager):
    """Manager com identificação por e-mail (doc 06 — User.email)."""

    use_in_migrations = True

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Usuário do domínio (doc 06 — User) com login por e-mail."""

    username = None  # login via e-mail
    email = models.EmailField(unique=True, verbose_name="e-mail")
    phone = models.CharField(max_length=20, blank=True, verbose_name="telefone")
    document = models.CharField(max_length=20, blank=True, verbose_name="documento")
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
        verbose_name="papel",
    )
    failed_login_attempts = models.PositiveSmallIntegerField(
        default=0, verbose_name="tentativas de login falhas"
    )
    locked_until = models.DateTimeField(null=True, blank=True, verbose_name="bloqueado até")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self):
        return self.get_full_name() or self.email

    @property
    def role_code(self):
        return self.role.code if self.role else None

    def is_locked(self) -> bool:
        return bool(self.locked_until and timezone.now() < self.locked_until)

    def remaining_lock_seconds(self) -> int:
        if not self.locked_until or timezone.now() >= self.locked_until:
            return 0
        return int((self.locked_until - timezone.now()).total_seconds())

    def register_failed_login(self) -> bool:
        """Registra falha; bloqueia a conta ao atingir MAX_LOGIN_ATTEMPTS.

        Retorna True se a conta acabou de ser bloqueada.
        """
        max_attempts = settings.MAX_LOGIN_ATTEMPTS
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = timezone.now() + timedelta(seconds=settings.LOCKOUT_SECONDS)
            self.save(update_fields=["failed_login_attempts", "locked_until"])
            return True
        self.save(update_fields=["failed_login_attempts"])
        return False

    def reset_failed_login(self) -> None:
        if self.failed_login_attempts or self.locked_until:
            self.failed_login_attempts = 0
            self.locked_until = None
            self.save(update_fields=["failed_login_attempts", "locked_until"])
