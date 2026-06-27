from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from apps.accounts.forms import ClientRegistrationForm, StyledAuthenticationForm
from apps.accounts.models import UserProfile


class AccountsLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        profile = getattr(self.request.user, "profile", None)
        if profile and profile.role == UserProfile.Role.GYM_STAFF:
            return reverse("dashboard:session_list")
        if (
            profile
            and profile.role == UserProfile.Role.CLIENT
            and profile.gym_id
        ):
            return reverse(
                "bookings:client_calendar",
                kwargs={"gym_slug": profile.gym.slug},
            )
        return super().get_success_url()


class AccountsLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")


def register_client(request, gym_slug=None):
    initial = {}
    if gym_slug:
        from apps.gyms.models import Gym

        gym = Gym.objects.filter(slug=gym_slug, is_active=True).first()
        if gym:
            initial["gym"] = gym.pk

    if request.method == "POST":
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            gym = form.cleaned_data["gym"]
            messages.success(request, "Registrazione completata.")
            return redirect("bookings:client_calendar", gym_slug=gym.slug)
    else:
        form = ClientRegistrationForm(initial=initial)

    return render(
        request,
        "accounts/register.html",
        {"form": form, "gym_slug": gym_slug},
    )
