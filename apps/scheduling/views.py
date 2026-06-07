from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

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