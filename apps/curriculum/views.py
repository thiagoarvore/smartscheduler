from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import SubjectForm, CurriculumMatrixForm
from .models import Subject, CurriculumMatrix


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


class CurriculumIndexView(LoginRequiredMixin, TemplateView):
    template_name = "curriculum/index.html"


class SubjectListView(TenantMixin, LoginRequiredMixin, ListView):
    model = Subject
    template_name = "schools/entity_list.html"
    context_object_name = "items"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["model_name"] = self.model._meta.model_name
        context["create_url_name"] = "curriculum:subject-list"
        context["update_url_name"] = "curriculum:subject-update"
        context["delete_url_name"] = "curriculum:subject-delete"
        return context


class SubjectCreateView(TenantMixin, LoginRequiredMixin, CreateView):
    model = Subject
    form_class = SubjectForm
    template_name = "schools/entity_form.html"
    success_url = reverse_lazy("curriculum:subject-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = "curriculum:subject-list"
        return context


class SubjectUpdateView(TenantMixin, LoginRequiredMixin, UpdateView):
    model = Subject
    form_class = SubjectForm
    template_name = "schools/entity_form.html"
    success_url = reverse_lazy("curriculum:subject-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = "curriculum:subject-list"
        return context


class SubjectDeleteView(TenantMixin, LoginRequiredMixin, DeleteView):
    model = Subject
    template_name = "schools/entity_confirm_delete.html"
    success_url = reverse_lazy("curriculum:subject-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = "curriculum:subject-list"
        return context


class CurriculumMatrixListView(TenantMixin, LoginRequiredMixin, ListView):
    model = CurriculumMatrix
    template_name = "schools/entity_list.html"
    context_object_name = "items"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["model_name"] = self.model._meta.model_name
        context["create_url_name"] = "curriculum:curriculummatrix-list"
        context["update_url_name"] = "curriculum:curriculummatrix-update"
        context["delete_url_name"] = "curriculum:curriculummatrix-delete"
        return context


class CurriculumMatrixCreateView(TenantMixin, LoginRequiredMixin, CreateView):
    model = CurriculumMatrix
    form_class = CurriculumMatrixForm
    template_name = "schools/entity_form.html"
    success_url = reverse_lazy("curriculum:curriculummatrix-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = "curriculum:curriculummatrix-list"
        return context


class CurriculumMatrixUpdateView(TenantMixin, LoginRequiredMixin, UpdateView):
    model = CurriculumMatrix
    form_class = CurriculumMatrixForm
    template_name = "schools/entity_form.html"
    success_url = reverse_lazy("curriculum:curriculummatrix-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = "curriculum:curriculummatrix-list"
        return context


class CurriculumMatrixDeleteView(TenantMixin, LoginRequiredMixin, DeleteView):
    model = CurriculumMatrix
    template_name = "schools/entity_confirm_delete.html"
    success_url = reverse_lazy("curriculum:curriculummatrix-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = "curriculum:curriculummatrix-list"
        return context