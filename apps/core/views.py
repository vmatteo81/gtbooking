from django.shortcuts import redirect, render

from apps.accounts.models import UserProfile
from apps.gyms.models import Gym


def home(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        if profile:
            if profile.role == UserProfile.Role.GYM_STAFF:
                return redirect("dashboard:session_list")
            if profile.role == UserProfile.Role.CLIENT and profile.gym:
                return redirect(
                    "bookings:client_calendar",
                    gym_slug=profile.gym.slug,
                )
    gyms = Gym.objects.filter(is_active=True).order_by("name")
    return render(request, "core/home.html", {"gyms": gyms})
