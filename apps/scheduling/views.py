from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from apps.scheduling.services.cooldown import check_cooldown
from apps.scheduling.tasks import run_3_variants
from apps.schools.models import SchoolYear

from .forms import SchoolYearForm


class TenantMixin:
    def get_tenant(self):
        return self.request.tenant

    def get_queryset(self):
        return super().get_queryset().filter(tenant=self.get_tenant())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        if not form.instance.pk:
            form.instance.tenant = self.get_tenant()
        return super().form_valid(form)


class SchedulingIndexView(LoginRequiredMixin, TemplateView):
    template_name = "scheduling/index.html"


class SchoolYearListView(TenantMixin, LoginRequiredMixin, ListView):
    model = SchoolYear
    template_name = "schools/entity_list.html"
    context_object_name = "items"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["model_name"] = self.model._meta.model_name
        context["create_url_name"] = "scheduling:schoolyear-list"
        context["update_url_name"] = "scheduling:schoolyear-update"
        context["delete_url_name"] = "scheduling:schoolyear-delete"
        return context


class SchoolYearCreateView(TenantMixin, LoginRequiredMixin, CreateView):
    model = SchoolYear
    form_class = SchoolYearForm
    template_name = "schools/entity_form.html"
    success_url = reverse_lazy("scheduling:schoolyear-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = "scheduling:schoolyear-list"
        return context


class SchoolYearUpdateView(TenantMixin, LoginRequiredMixin, UpdateView):
    model = SchoolYear
    form_class = SchoolYearForm
    template_name = "schools/entity_form.html"
    success_url = reverse_lazy("scheduling:schoolyear-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = "scheduling:schoolyear-list"
        return context


class SchoolYearDeleteView(TenantMixin, LoginRequiredMixin, DeleteView):
    model = SchoolYear
    template_name = "schools/entity_confirm_delete.html"
    success_url = reverse_lazy("scheduling:schoolyear-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = "scheduling:schoolyear-list"
        return context

# Sprint 08 — Solver UI (SDD §22.2.2)
# -----------------------------------------------------------------------


class RunTimetableView(TenantMixin, LoginRequiredMixin, View):
    """POST /scheduling/run/<school_year_id>/ — dispara a geração.

    Lógica (Sprint 08 item 3.11):
    1. Verifica cooldown
    2. Se bloqueado: redireciona com mensagem de erro
    3. Se liberado: dispara `run_3_variants` (síncrono no MVP)
    4. Redireciona pra página de progresso
    """

    def post(self, request, school_year_id) -> HttpResponse:
        school_year = SchoolYear.objects.filter(
            id=school_year_id,
            tenant=self.get_tenant(),
        ).first()
        if school_year is None:
            messages.error(request, "Ano letivo não encontrado.")
            return HttpResponse(status=404)

        cooldown = check_cooldown(school_year)
        if not cooldown.pode_rodar:
            messages.error(request, cooldown.mensagem)
            return HttpResponse(status=429)  # Too Many Requests — semântica de rate limit

        # Dispara o pipeline (Sprint 08 — síncrono; Sprint 09+ vira Celery)
        try:
            run_ids = run_3_variants(
                school_year_id=str(school_year.id),
                disparado_por="user",
                user_id=str(request.user.id) if request.user.is_authenticated else None,
            )
        except ValueError as exc:
            messages.error(request, str(exc))
            return HttpResponse(status=400)
        request.session["solver_run_ids"] = run_ids
        return HttpResponse(
            status=302,
            headers={"Location": reverse("scheduling:run-progress", args=[school_year.id])},
        )


class RunProgressView(TenantMixin, LoginRequiredMixin, TemplateView):
    """GET /scheduling/run/<school_year_id>/progress/ — polling HTMX.

    Mostra o status atual das 3 runs. HTMX dá refresh a cada 5s.
    Quando todas terminarem, redireciona pra `run-result`.
    """

    template_name = "scheduling/run_progress.html"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        school_year = SchoolYear.objects.get(
            id=kwargs["school_year_id"],
            tenant=self.get_tenant(),
        )
        run_ids = self.request.session.get("solver_run_ids", [])
        from .models import SolverRun

        runs = SolverRun.objects.filter(id__in=run_ids).select_related("variant")
        context["school_year"] = school_year
        context["runs"] = runs
        context["all_done"] = all(r.is_terminal for r in runs) if runs else False
        return context


class RunResultViewActual(TenantMixin, LoginRequiredMixin, DetailView):
    """GET /scheduling/run/<school_year_id>/result/ — grade visual.

    Sprint 08 item 3.13: renderiza a grade semanal da vencedora.
    Identifica a vencedora como o SolverRun com menor nº de buracos
    entre os runs da última execução; empate = menor tempo total.
    """

    template_name = "scheduling/run_result.html"
    model = SchoolYear
    slug_field = "id"
    slug_url_kwarg = "school_year_id"

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        school_year = self.get_object()
        from .models import SolverRun

        runs = (
            SolverRun.objects.filter(
                school_year=school_year,
                status=SolverRun.StatusChoices.SUCCESS,
            )
            .order_by("created_at")
            .select_related("variant")
        )
        # Critério de vitória (SDD §22.2.10): menos buracos, desempate por tempo
        runs_list = list(runs)
        runs_list.sort(
            key=lambda r: (
                r.buracos if r.buracos is not None else 999_999,
                r.tempo_total.total_seconds() if r.tempo_total else 999_999,
            )
        )
        winning_run = runs_list[0] if runs_list else None

        context["school_year"] = school_year
        context["runs"] = runs_list
        context["winning_run"] = winning_run

        # Sprint 09 — Sugestões (SDD §22.4)
        if winning_run:
            from .models import Suggestion

            suggestions = Suggestion.objects.filter(
                solver_run=winning_run,
                status=Suggestion.StatusChoices.PENDING,
            ).order_by("-delta")
            context["suggestions"] = suggestions
            context["suggestions_count"] = suggestions.count()
        else:
            context["suggestions"] = []
            context["suggestions_count"] = 0

        return context


# Sprint 09 — Sugestões (SDD §22.4)
# -----------------------------------------------------------------------


def suggestion_detail_view(request, pk):
    """GET /scheduling/suggestion/<uuid:pk>/ — partial HTML for HTMX modal."""
    from .models import Suggestion

    suggestion = get_object_or_404(Suggestion, pk=pk)
    return render(request, "scheduling/suggestion_detail.html", {"suggestion": suggestion})


def suggestion_ignore_view(request, pk):
    """POST /scheduling/suggestion/<uuid:pk>/ignore/ — mark suggestion as ignored.

    Sets status='ignored' and aplicado_em=now(), then returns an HTMX swap
    that removes the element from the list.
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    from .models import Suggestion

    suggestion = get_object_or_404(Suggestion, pk=pk)
    suggestion.status = Suggestion.StatusChoices.IGNORED
    suggestion.aplicado_em = timezone.now()
    suggestion.save(update_fields=["status", "aplicado_em", "updated_at"])
    # HTMX outer-swap: returns an empty div with the same id so the row disappears
    return HttpResponse(f'<div id="suggestion-{pk}"></div>')
