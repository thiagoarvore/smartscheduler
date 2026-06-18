# Sprint 02 — App `accounts` + App `schools` + Middleware híbrido

> **Branch**: `sprint-02/accounts-e-schools`
> **Objetivo**: ter os apps de domínio base. `accounts` é app marcador (auth vem do `django_base_kit`). `schools` cria a escola de **cada user criado por mim (admin)** — relação 1:1. **Toda view autenticada ganha `request.school` via middleware**, e listagens escopam via mixin.

## 1. Princípios desta sprint

- **Sem over-engineering**. Só o que precisa existir pra próxima sprint (Sprint 03 — unidades, séries, turmas) ter onde morar.
- `accounts` aproveita o `django_base_kit` (que já entrega signup/login/logout/reset). Sprint adiciona **só**: nada (é app marcador nesta sprint).
- `schools` é CRUD mínimo: nome + dados de contato da escola. **Eu (admin) crio a escola via admin Django e vinculo ao user**. User não cria.
- **Não tem multi-tenant**. Cada user tem 1 escola, é o dono total.
- **Não tem multi-user por escola** nesta sprint.
- **Abordagem híbrida pra escopo de escola**:
  - **Middleware** carrega `request.school` em toda request autenticada, depois do `AuthenticationMiddleware`.
  - **Mixin** `SchoolScopedQuerysetMixin` filtra querysets de models filhos de `School` por `owner=request.user`. Views que listam coisas usam o mixin.
  - Views que só leem `request.school.X` (nome, CNPJ, etc.) confiam no middleware.
  - Views públicas (`/health/`, login, signup, reset) **não passam pelo middleware** (são isentas por path).

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
│  ├─ middleware.py             # NOVO — SchoolMiddleware
│  ├─ mixins.py                 # NOVO — SchoolScopedQuerysetMixin
│  ├─ models.py
│  ├─ tests/                    # NOVO
│  │  ├─ __init__.py
│  │  ├─ test_school_model.py
│  │  ├─ test_school_signals.py
│  │  ├─ test_school_views.py
│  │  ├─ test_school_middleware.py   # NOVO
│  │  └─ test_school_mixins.py       # NOVO
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
- Único ajuste garantido: `LoginView` redireciona pra `/` (e lá vê se o user tem escola — se não, não deixa fazer nada enquanto o admin do sistema não criar a escola do user).

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

### 4.2 Middleware (`schools/middleware.py`)

**Escolha de design**: middleware roda **depois** de `AuthenticationMiddleware`, **antes** de qualquer view. Em toda request:

1. Se `request.user` é anônimo → `request.school = None`, segue.
2. Se path é público (`/health/`, `/admin/`, `/accounts/login/`, `/accounts/signup/`, `/accounts/logout/`, `/reset_password/*`) → `request.school = None`, segue (não precisa de escola).
3. Senão, `request.school = request.user.school` (ou `None` se user não tem escola).
4. Se a view requer escola (definida por atributo `requires_school = True` na view ou por path) **e** `request.school is None` → raise 404.

```python
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


PUBLIC_PATH_PREFIXES = (
    "/health/",
    "/admin/",
    "/static/",
    "/media/",
    "/accounts/login/",
    "/accounts/logout/",
    "/reset_password/",
)


class SchoolMiddleware(MiddlewareMixin):
    """
    Carrega request.school para toda request autenticada.
    Views públicas (login, signup, health, admin) não recebem request.school.
    """

    def process_request(self, request):
        request.school = None
        if not request.user.is_authenticated:
            return
        path = request.path
        for prefix in PUBLIC_PATH_PREFIXES:
            if path.startswith(prefix):
                return
        # Tenta pegar a escola do user. Pode não existir (admin sem escola).
        request.school = getattr(request.user, "school", None)
```

> **Decisão**: middleware **não força** que toda view tenha escola. Views que precisam **declaram** (ou via atributo na view, ou via path — Sprint futura). Se a view não declara, `request.school` pode ser `None` sem erro.

> **Decisão 2**: order em `MIDDLEWARE` = **depois** de `AuthenticationMiddleware`, **antes** de qualquer coisa que leia `request.school`. Lista concreta em §5.

### 4.3 Mixin (`schools/mixins.py`)

```python
class SchoolScopedQuerysetMixin:
    """
    Filtra o queryset da view por owner=request.user.
    Use em DetailView/ListView/UpdateView/DeleteView de models filhos de School.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return qs.none()
        return qs.filter(owner=self.request.user)
```

> **Por que mixin e não middleware**: o mixin é **opt-in** (só quem herda usa). Middleware seria forçado em todas as views, e views que listam coisas de fora (admin, API) iam quebrar.

### 4.4 Forms (`schools/forms.py`)

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

### 4.5 Views (`schools/views.py`)

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView

from .forms import SchoolForm
from .mixins import SchoolScopedQuerysetMixin
from .models import School


class SchoolDetailView(
    LoginRequiredMixin, SchoolScopedQuerysetMixin, DetailView
):
    model = School
    template_name = "schools/school_detail.html"
    context_object_name = "school"


class SchoolUpdateView(
    LoginRequiredMixin, SchoolScopedQuerysetMixin, UpdateView
):
    model = School
    form_class = SchoolForm
    template_name = "schools/school_form.html"
    context_object_name = "school"

    def get_success_url(self):
        return self.object.get_absolute_url()
```

> **Decisão**: **removido `SchoolCreateView`**. Quem cria a escola sou **eu** (admin Django). User não tem acesso a `/schools/new/`. Se ele tentar acessar direto, o mixin retorna 404.

> **Decisão 2**: views de `schools` **confiam no middleware** pra carregar `request.school`. Não fazem `get_queryset().filter(owner=)` direto — o mixin faz. `request.school` é usado pra mostrar nome/CNPJ/etc. no template.

> **Decisão 3**: detalhe e update escopam por owner. Se o user logado não é dono da escola no URL, mixin retorna 404.

### 4.6 URLs (`schools/urls.py`)

```python
from django.urls import path

from . import views

app_name = "schools"

urlpatterns = [
    # raiz: redireciona pra /schools/<uuid-do-user>/
    # (resolvido no Sprint 03 com um redirect view)
    path("<uuid:pk>/", views.SchoolDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.SchoolUpdateView.as_view(), name="update"),
]
```

`app/urls.py` ganha:
```python
path("schools/", include("schools.urls", namespace="schools")),
```

> **Decisão**: `path("")` em `schools.urls` (raiz) **fica pra Sprint 03** — vai virar um redirect que detecta `request.school` (via middleware) e redireciona pra `/schools/<uuid>/`. Mantém a sprint 2 enxuta.
(Pode trazer isso aqui para essa sprint)

### 4.7 Templates

- `templates/schools/school_form.html` — form genérico de update
- `templates/schools/school_detail.html` — mostra `{{ school.name }}`, CNPJ, telefone, email, endereço + link "Editar"

Mínimo: 1 arquivo por template, sem herança complexa (sem `base.html` nesta sprint — Sprint 03 ou 04 traz layout base do `django_base_kit`).

### 4.8 Admin (`schools/admin.py`)

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

> **Decisão**: admin é onde **eu crio a escola do user**. User não vê nem chega ao admin (não é superuser). O fluxo é: admin Django → cria user → cria School vinculado a esse user → user loga e tem `request.school`.

### 4.9 Testes

**`test_school_model.py`** (2 testes):
- `test_school_str_returns_name`
- `test_school_has_one_to_one_owner` (relação reversa `user.school`)

**`test_school_signals.py`** (1 teste):
- `test_school_inherits_basemodel_fields` (verifica UUID + created_at + updated_at + active)

**`test_school_views.py`** (3 testes):
- `test_detail_view_requires_login`
- `test_detail_view_filters_by_owner` (outro user recebe 404)
- `test_update_view_filters_by_owner`

**`test_school_middleware.py`** (4 testes):
- `test_middleware_sets_school_for_authenticated_user_with_school`
- `test_middleware_sets_school_none_for_user_without_school`
- `test_middleware_skips_anon_user`
- `test_middleware_skips_public_paths` (`/health/`, `/admin/`, `/accounts/login/`)

**`test_school_mixins.py`** (2 testes):
- `test_mixin_filters_queryset_by_owner`
- `test_mixin_returns_empty_for_anon_user`

**Total**: 12 testes.

## 5. Configuração (`app/settings.py`)

### 5.1 INSTALLED_APPS

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

### 5.2 MIDDLEWARE (ordem importa!)

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # ← request.user existe aqui
    "schools.middleware.SchoolMiddleware",                     # ← request.school existe aqui
    "auditlog.middleware.AuditlogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]
```

> **Ordem crítica**: `SchoolMiddleware` vem **depois** de `AuthenticationMiddleware` (precisa de `request.user`) e **antes** de qualquer coisa que leia `request.school`. No momento nenhum outro middleware lê, mas Sprint 03+ vai.

## 6. Critérios de aceite

- [ ] `docker compose up --build` sobe sem erros
- [ ] `python manage.py check` retorna 0 issues
- [ ] `python manage.py makemigrations` gera migrations para `schools` (e só `schools`)
- [ ] `python manage.py migrate` aplica tudo
- [ ] `ruff check .` passa
- [ ] `pytest` passa (2 testes de `accounts` + 12 de `schools` = 14 novos testes verdes)
- [ ] `curl http://localhost:8000/health/` retorna `{"status": "ok"}`
- [ ] Admin Django cria `User` e `School` vinculado
- [ ] User comum **não** tem acesso a `/admin/` (não é superuser)
- [ ] User comum **não** tem acesso a `/schools/new/` (rota não existe)
- [ ] `/schools/<uuid>/` (dono autenticado) mostra escola
- [ ] `/schools/<uuid>/` (outro user) retorna 404
- [ ] `/schools/<uuid>/` (não autenticado) redireciona para login
- [ ] `/accounts/login/`, `/accounts/signup/`, `/health/`, `/admin/` **não** setam `request.school` (middleware isenta)
- [ ] `request.school` está setado em qualquer view autenticada (testado via request factory)
- [ ] Reset de senha continua funcionando (templates `django_base_kit`)

## 7. Fora de escopo desta sprint

- Layout base / tema visual (Sprint 03 ou 04)
- Auto-create de `School` no signup (user não cria escola — admin cria)
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
- Redirect na raiz `/schools/` → `/schools/<uuid>/` (Sprint 03)
- Forçar view a exigir escola via atributo `requires_school` (Sprint 03+, quando models filhos existirem)
- Tela de "user sem escola" / wizard de criar escola (não existe, admin sempre cria)

## 8. Notas

- **Não** criar `accounts/models.py` com model custom. `User` é do `base_kit`. App `accounts` é um **marcador** para extensões futuras de auth.
- **Não** criar `tenant.py`, `middleware.py` de tenant, ou qualquer abstração de multi-tenant. Repetindo: sem multi-tenant.
- **Não** adicionar `school_id` como FK em outros models nesta sprint. `School` ainda não tem filhos. Sprint 03+ faz isso pra `Unit`, `Series`, etc.
- A herança de `BaseModel` já dá auditlog automático. Não registrar `School` em `auditlog.register` separadamente (audita via herança).
- **Middleware não força** que toda view tenha escola. Se a view não precisa, `request.school` pode ser `None` sem erro. Sprint 03+ adiciona o atributo `requires_school` quando models filhos de `School` começarem a aparecer.
- **Mixin é opt-in**: views que listam coisas de fora (admin, API) NÃO herdam o mixin. Só views de usuário final escopam.
- **Fluxo de criação de escola**: admin Django (`/admin/`) → cria `User` → cria `School` vinculado a esse user → user loga → `request.school` aparece via middleware.
