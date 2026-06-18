from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views.generic import DetailView, UpdateView, View

from .forms import SchoolForm
from .mixins import SchoolScopedQuerysetMixin
from .models import School


class SchoolRedirectView(LoginRequiredMixin, View):
    """
    /  →  /schools/<uuid>/  (se tem escola)
       →  schools/no_school.html  (se logado mas sem escola)
    """

    def get(self, request, *args, **kwargs):
        if request.school is None:
            return render(request, "schools/no_school.html", status=200)
        return redirect("schools:detail", pk=request.school.pk)


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
