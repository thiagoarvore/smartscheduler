from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import TeacherAvailabilityForm, TeacherForm, TeacherQualificationForm
from .models import Teacher, TeacherAvailability, TeacherQualification


class PeopleIndexView(LoginRequiredMixin, TemplateView):
    template_name = "people/index.html"


class PeopleEntityListView(LoginRequiredMixin, ListView):
    template_name = "schools/entity_list.html"
    context_object_name = "items"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["model_name"] = self.model._meta.model_name
        context["create_url_name"] = self.create_url_name
        context["update_url_name"] = f"people:{self.model._meta.model_name}-update"
        context["delete_url_name"] = f"people:{self.model._meta.model_name}-delete"
        return context


class PeopleEntityCreateView(LoginRequiredMixin, CreateView):
    template_name = "schools/entity_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = self.list_url_name
        return context


class PeopleEntityUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "schools/entity_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = self.list_url_name
        return context


class PeopleEntityDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "schools/entity_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = self.list_url_name
        return context


class TeacherListView(PeopleEntityListView):
    model = Teacher
    create_url_name = "people:teacher-create"


class TeacherCreateView(PeopleEntityCreateView):
    model = Teacher
    form_class = TeacherForm
    success_url = reverse_lazy("people:teacher-list")
    list_url_name = "people:teacher-list"


class TeacherUpdateView(PeopleEntityUpdateView):
    model = Teacher
    form_class = TeacherForm
    success_url = reverse_lazy("people:teacher-list")
    list_url_name = "people:teacher-list"


class TeacherDeleteView(PeopleEntityDeleteView):
    model = Teacher
    success_url = reverse_lazy("people:teacher-list")
    list_url_name = "people:teacher-list"


class TeacherQualificationListView(PeopleEntityListView):
    model = TeacherQualification
    create_url_name = "people:teacherqualification-create"


class TeacherQualificationCreateView(PeopleEntityCreateView):
    model = TeacherQualification
    form_class = TeacherQualificationForm
    success_url = reverse_lazy("people:teacherqualification-list")
    list_url_name = "people:teacherqualification-list"


class TeacherQualificationUpdateView(PeopleEntityUpdateView):
    model = TeacherQualification
    form_class = TeacherQualificationForm
    success_url = reverse_lazy("people:teacherqualification-list")
    list_url_name = "people:teacherqualification-list"


class TeacherQualificationDeleteView(PeopleEntityDeleteView):
    model = TeacherQualification
    success_url = reverse_lazy("people:teacherqualification-list")
    list_url_name = "people:teacherqualification-list"


class TeacherAvailabilityListView(PeopleEntityListView):
    model = TeacherAvailability
    create_url_name = "people:teacheravailability-create"


class TeacherAvailabilityCreateView(PeopleEntityCreateView):
    model = TeacherAvailability
    form_class = TeacherAvailabilityForm
    success_url = reverse_lazy("people:teacheravailability-list")
    list_url_name = "people:teacheravailability-list"


class TeacherAvailabilityUpdateView(PeopleEntityUpdateView):
    model = TeacherAvailability
    form_class = TeacherAvailabilityForm
    success_url = reverse_lazy("people:teacheravailability-list")
    list_url_name = "people:teacheravailability-list"


class TeacherAvailabilityDeleteView(PeopleEntityDeleteView):
    model = TeacherAvailability
    success_url = reverse_lazy("people:teacheravailability-list")
    list_url_name = "people:teacheravailability-list"
