# Sprint 02 — App `accounts` + App `schools`

> **Branch**: `sprint-02/accounts-e-schools`
> **Objetivo**: ter os apps de domínio base. `accounts` centraliza a redefinição/reset de senha (customizando o que o `django_base_kit` entrega). `schools` cria a escola de cada user (relação 1:1 — `School.owner = ForeignKey(User, unique=True)`).

## 1. Princípios desta sprint

- **Sem over-engineering**. Só o que precisa existir pra próxima sprint (Sprint 03 — unidades, séries, turmas) ter onde morar.
- `accounts` aproveita o `django_base_kit` (que já entrega signup/login/logout/reset). Sprint adiciona **só**: integração com o modelo `School` e ajustes pontuais.
- `schools` é CRUD mínimo: nome + dados de contato da escola + dono.
- **Não tem multi-tenant**. Cada user tem 1 escola, é o dono total.
- **Não tem multi-user por escola** nesta sprint.
- Admin do Django liberado para `accounts.User` e `schools.School` (a próxima sprint refina isso).

## 2. Estrutura de diretórios

```
smartscheduler/
├─ accounts/                    # NOVO
│  ├─ __init__.py
│  ├─ admin.py
│  ├─ apps.py
│  ├─ forms.py
│  ├─ models.py                 # vazio (User vem do django_base_kit)
│  ├─ tests/                    # NOVO
│  │  ├─ __init__.py
│  │  └─ test_signup.py
│  ├─ urls.py
│  └─ views.py
├─ schools/                     # NOVO
│  ├─ __init__.py
│  ├─ admin.py
│  ├─ apps.py
│  ├─ forms.py
│  ├─ models.py
│  ├─ signals.py
│  ├─ tests/                    # NOVO
│  │  ├─ __init__.py
│  │  ├─ test_school_model.py
│  │  ├─ test_school_signals.py
│  │  └─ test_school_views.py
│  ├─ urls.py
│  └─ views.py
└─ app/
   └─ settings.py               # edita: INSTALLED_APPS, AUTH_USER_MODEL
```

## 3. App `accounts`

### 3.1 Responsabilidade

- Centralizar URLs de auth customizadas (caso a UI do `django_base_kit` precise de ajuste de layout).
- Garantir que **após signup, o user é redirecionado pro wizard de criar escola** (próxima sprint faz o wizard; por ora, redireciona pra `/schools/new/` que já funciona com `SchoolCreateView`).
- Garantir que **reset de senha funciona ponta-a-ponta** (email + link + form de nova senha), com templates próprios.

### 3.2 Models

**Nada.** O `User` continua sendo `base_kit.User` (UUID, email único, `AbstractUser` + `BaseModel`).

### 3.3 Views

- `views.py` herda do `django_base_kit` quando possível. Se não precisar customizar, não criar.
- Único ajuste garantido: `LoginView` redireciona pra `/` (e lá vê se o user tem escola — se não, sugere criar).

### 3.4 Forms

- `forms.py` herda `base_kit.forms.SignUpForm` e `base_kit.forms.UserLoginForm`.
- Nenhum campo customizado nesta sprint.

### 3.5 URLs (`accounts/urls.py`)

```python
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # Herda do django_base_kit.urls.user_urlpatterns
    # (mantemos a URL /accounts/login/ via app.urls include)
]
```

> **Decisão**: como o `django_base_kit` já entrega `user_urlpatterns` com `/accounts/login/`, `/accounts/logout/`, `/accounts/signup/`, etc., **a `app/urls.py` continua incluindo `user_urlpatterns` direto**. Não criamos `accounts/urls.py` nesta sprint. O app `accounts` existe pra **sprints futuras** que precisem estender auth (ex: convidar professor, social login).

**Resultado**: `accounts/` vira só um app marcador com `__init__.py` + `apps.py` + `tests/__init__.py` + `admin.py` (registra `User` do `base_kit`). **Sem models, sem views, sem forms nesta sprint.**

### 3.6 Admin

- Registra `base_kit.User` com `UserAdmin` padrão do Django (suficiente — próxima sprint customiza se precisar).

### 3.7 Testes

- 1 teste: `test_signup_creates_user_with_email_unique` — confirma que `SignUpForm` cria user com email único (validação do `base_kit`).
- 1 teste: `test_login_redirects_to_home` — confirma que login redireciona pra `/`.
- Total: 2 testes.

## 4. App `schools`

### 4.1 Modelo (`schools/models.py`)

```python
import uuid

from django.conf import settings
from django.db import models

from django_base_kit.models import BaseModel


class School(BaseModel):
    """
    A escola de um único user.
    Relação 1:1 — cada user é dono de no máximo 1 escola.
    """
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="school",
    )
    name = models.CharField("Nome", max_length=200)
    cnpj = models.CharField("CNPJ", max_length=18, blank=True)
    phone = models.CharField("Telefone", max_length=20, blank=True)
    email = models.EmailField("E-mail de contato", blank=True)
    address = models.CharField("Endereço", max_length=255, blank=True)

    class Meta:
        verbose_name = "Escola"
        verbose_name_plural = "Escolas"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        from django.urls import reverse
        return reverse("schools:detail", kwargs={"pk": self.pk})
```

> **Decisão**: `School` herda de `BaseModel` (do `django_base_kit`) — ganha UUID, `created_at`, `updated_at`, `active`, e auditlog de graça. **Não duplicar esses campos**.

> **Decisão 2**: usar `OneToOneField` direto no `owner`, sem `Tenant` abstrato. Alinhado com o PRD (sem multi-tenant).

### 4.2 Signals (`schools/signals.py`)

**Sem signals nesta sprint.** A criação de `School` é feita explicitamente quando o user clica em "Criar escola". Sprint 03+ pode adicionar auto-create no signup se virar requisito.

### 4.3 Forms (`schools/forms.py`)

```python
from django import forms

from .models import School


class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ["name", "cnpj", "phone", "email", "address"]
        labels = {
            "name": "Nome da escola",
            "cnpj": "CNPJ",
            "phone": "Telefone",
            "email": "E-mail de contato",
            "address": "Endereço",
        }
```

### 4.4 Views (`schools/views.py`)

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import SchoolForm
from .models import School


class SchoolCreateView(LoginRequiredMixin, CreateView):
    model = School
    form_class = SchoolForm
    template_name = "schools/school_form.html"
    success_url = reverse_lazy("schools:detail")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class SchoolDetailView(LoginRequiredMixin, DetailView):
    model = School
    template_name = "schools/school_detail.html"

    def get_queryset(self):
        return School.objects.filter(owner=self.request.user)


class SchoolUpdateView(LoginRequiredMixin, UpdateView):
    model = School
    form_class = SchoolForm
    template_name = "schools/school_form.html"

    def get_queryset(self):
        return School.objects.filter(owner=self.request.user)

    def get_success_url(self):
        return self.object.get_absolute_url()
```

> **Decisão**: `LoginRequiredMixin` em **toda** view. `get_queryset` filtra por `owner=request.user` (user não vê escola dos outros, mesmo se adivinhar o ID — não há "outros" sem multi-tenant, mas a checagem é obrigatória por segurança).

### 4.5 URLs (`schools/urls.py`)

```python
from django.urls import path

from . import views

app_name = "schools"

urlpatterns = [
    path("new/", views.SchoolCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.SchoolDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.SchoolUpdateView.as_view(), name="update"),
]
```

`app/urls.py` ganha:
```python
path("", include("schools.urls", namespace="schools")),
```

### 4.6 Templates

- `templates/schools/school_form.html` — form genérico de create/update
- `templates/schools/school_detail.html` — mostra os dados da escola + link "Editar"

Mínimo: 1 arquivo por template, sem herança complexa (sem `base.html` nesta sprint — Sprint 03 ou 04 traz layout base do `django_base_kit`).

### 4.7 Admin (`schools/admin.py`)

```python
from django.contrib import admin

from .models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "phone", "email", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("name", "cnpj", "email")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("owner",)
```

### 4.8 Testes

**`test_school_model.py`** (2 testes):
- `test_school_str_returns_name`
- `test_school_has_one_to_one_owner` (relação reversa `user.school`)

**`test_school_signals.py`** (1 teste):
- `test_school_inherits_basemodel_fields` (verifica UUID + created_at + updated_at + active)

**`test_school_views.py`** (4 testes):
- `test_create_view_assigns_owner_to_logged_user`
- `test_create_view_redirects_to_detail`
- `test_detail_view_filters_by_owner` (outro user não vê)
- `test_update_view_filters_by_owner`

**Total**: 7 testes.

## 5. Configuração (`app/settings.py`)

```python
INSTALLED_APPS = [
    # ... django.contrib.* ...
    # ... third-party ...

    # Local
    "accounts",
    "schools",
]
```

`AUTH_USER_MODEL` continua `"base_kit.User"` (já configurado na Sprint 01).

## 6. Critérios de aceite

- [ ] `docker compose up --build` sobe sem erros
- [ ] `python manage.py check` retorna 0 issues
- [ ] `python manage.py makemigrations` gera migrations para `schools` (e só `schools`)
- [ ] `python manage.py migrate` aplica tudo
- [ ] `ruff check .` passa
- [ ] `pytest` passa (2 testes de `accounts` + 7 de `schools` = 9 novos testes verdes)
- [ ] `curl http://localhost:8000/health/` retorna `{"status": "ok"}`
- [ ] `/schools/new/` (autenticado) cria escola e vincula ao `request.user`
- [ ] `/schools/new/` (não autenticado) redireciona para `/accounts/login/?next=/schools/new/`
- [ ] `/schools/<uuid>/` (dono) mostra escola
- [ ] `/schools/<uuid>/` (outro user) retorna 404
- [ ] Admin Django mostra `Schools` e `User` (do `base_kit`)
- [ ] Reset de senha continua funcionando (templates `django_base_kit`)

## 7. Fora de escopo desta sprint

- Layout base / tema visual (Sprint 03 ou 04)
- Wizard de criação de escola (próxima sprint pode virar wizard, mas o create simples já basta)
- Auto-create de `School` no signup via signal
- Multi-user por escola
- `Unit`, `Series`, `ClassGroup`, `Subject`, `Teacher` (Sprint 03+)
- `WorkloadItem` / grade horária (sprints seguintes)
- `SchoolYear` (FORA do MVP, conforme PRD)
- Customização de `UserAdmin` (basta o padrão nesta sprint)
- `AUDITLOG_TRACKING` detalhado para `School` (Sprint 03+ se necessário)
- Internacionalização adicional (mantém pt-BR hardcoded)
- `Account` abstraction (temos `User` direto)
- Permissões granulares (apenas dono acessa, sem papéis nesta sprint)
- API REST (sprint futura, se necessário)

## 8. Notas

- **Não** criar `accounts/models.py` com model custom. `User` é do `base_kit`. App `accounts` é um **marcador** para extensões futuras de auth.
- **Não** criar `tenant.py`, `middleware.py`, ou qualquer abstração de multi-tenant. Repetindo: sem multi-tenant.
- **Não** adicionar `school_id` como FK em outros models nesta sprint. `School` ainda não tem filhos. Sprint 03+ faz isso pra `Unit`, `Series`, etc.
- A herança de `BaseModel` já dá auditlog automático. Não registrar `School` em `auditlog.register` separadamente (audita via herança).
