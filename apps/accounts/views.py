from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import FormView

from .forms import UserLoginForm


class LoginView(FormView):
    """Handle user login via email."""

    form_class = UserLoginForm
    template_name = "accounts/login.html"
    success_url = "/"

    def form_valid(self, form):
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        user = authenticate(username=username, password=password)
        if user is not None:
            login(self.request, user)
            return super().form_valid(form)
        return self.form_invalid(form)


class LogoutView(View):
    """Log the user out and redirect to login."""

    def get(self, request):
        logout(request)
        return redirect("login")


@method_decorator(login_required(login_url="/accounts/login/"), name="dispatch")
class HomeView(View):
    """Simple home page after login."""

    def get(self, request):
        return render(request, "home.html")
