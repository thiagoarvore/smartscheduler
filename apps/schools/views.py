from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import ClassGroupForm, PeriodForm, SeriesForm, TeachingLevelForm, UnitForm
from .models import ClassGroup, Period, Series, TeachingLevel, Unit


class SchoolsIndexView(LoginRequiredMixin, TemplateView):
    template_name = "schools/index.html"


class SchoolEntityListView(LoginRequiredMixin, ListView):
    template_name = "schools/entity_list.html"
    context_object_name = "items"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["model_name"] = self.model._meta.model_name
        context["create_url_name"] = self.create_url_name
        context["update_url_name"] = f"schools:{self.model._meta.model_name}-update"
        context["delete_url_name"] = f"schools:{self.model._meta.model_name}-delete"
        return context


class SchoolEntityCreateView(LoginRequiredMixin, CreateView):
    template_name = "schools/entity_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = self.list_url_name
        return context


class SchoolEntityUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "schools/entity_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = self.list_url_name
        return context


class SchoolEntityDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "schools/entity_confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_verbose_name"] = self.model._meta.verbose_name
        context["list_url_name"] = self.list_url_name
        return context


class UnitListView(SchoolEntityListView):
    model = Unit
    create_url_name = "schools:unit-create"


class UnitCreateView(SchoolEntityCreateView):
    model = Unit
    form_class = UnitForm
    success_url = reverse_lazy("schools:unit-list")
    list_url_name = "schools:unit-list"


class UnitUpdateView(SchoolEntityUpdateView):
    model = Unit
    form_class = UnitForm
    success_url = reverse_lazy("schools:unit-list")
    list_url_name = "schools:unit-list"


class UnitDeleteView(SchoolEntityDeleteView):
    model = Unit
    success_url = reverse_lazy("schools:unit-list")
    list_url_name = "schools:unit-list"


class TeachingLevelListView(SchoolEntityListView):
    model = TeachingLevel
    create_url_name = "schools:teachinglevel-create"


class TeachingLevelCreateView(SchoolEntityCreateView):
    model = TeachingLevel
    form_class = TeachingLevelForm
    success_url = reverse_lazy("schools:teachinglevel-list")
    list_url_name = "schools:teachinglevel-list"


class TeachingLevelUpdateView(SchoolEntityUpdateView):
    model = TeachingLevel
    form_class = TeachingLevelForm
    success_url = reverse_lazy("schools:teachinglevel-list")
    list_url_name = "schools:teachinglevel-list"


class TeachingLevelDeleteView(SchoolEntityDeleteView):
    model = TeachingLevel
    success_url = reverse_lazy("schools:teachinglevel-list")
    list_url_name = "schools:teachinglevel-list"


class PeriodListView(SchoolEntityListView):
    model = Period
    create_url_name = "schools:period-create"


class PeriodCreateView(SchoolEntityCreateView):
    model = Period
    form_class = PeriodForm
    success_url = reverse_lazy("schools:period-list")
    list_url_name = "schools:period-list"


class PeriodUpdateView(SchoolEntityUpdateView):
    model = Period
    form_class = PeriodForm
    success_url = reverse_lazy("schools:period-list")
    list_url_name = "schools:period-list"


class PeriodDeleteView(SchoolEntityDeleteView):
    model = Period
    success_url = reverse_lazy("schools:period-list")
    list_url_name = "schools:period-list"


class SeriesListView(SchoolEntityListView):
    model = Series
    create_url_name = "schools:series-create"


class SeriesCreateView(SchoolEntityCreateView):
    model = Series
    form_class = SeriesForm
    success_url = reverse_lazy("schools:series-list")
    list_url_name = "schools:series-list"


class SeriesUpdateView(SchoolEntityUpdateView):
    model = Series
    form_class = SeriesForm
    success_url = reverse_lazy("schools:series-list")
    list_url_name = "schools:series-list"


class SeriesDeleteView(SchoolEntityDeleteView):
    model = Series
    success_url = reverse_lazy("schools:series-list")
    list_url_name = "schools:series-list"


class ClassGroupListView(SchoolEntityListView):
    model = ClassGroup
    create_url_name = "schools:classgroup-create"


class ClassGroupCreateView(SchoolEntityCreateView):
    model = ClassGroup
    form_class = ClassGroupForm
    success_url = reverse_lazy("schools:classgroup-list")
    list_url_name = "schools:classgroup-list"


class ClassGroupUpdateView(SchoolEntityUpdateView):
    model = ClassGroup
    form_class = ClassGroupForm
    success_url = reverse_lazy("schools:classgroup-list")
    list_url_name = "schools:classgroup-list"


class ClassGroupDeleteView(SchoolEntityDeleteView):
    model = ClassGroup
    success_url = reverse_lazy("schools:classgroup-list")
    list_url_name = "schools:classgroup-list"
