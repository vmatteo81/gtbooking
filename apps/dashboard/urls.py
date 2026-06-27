from django.urls import path

from apps.dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.StaffSessionListView.as_view(), name="session_list"),
    path("sessions/<int:pk>/", views.StaffSessionDetailView.as_view(), name="session_detail"),
    path(
        "sessions/<int:pk>/bookings/<int:booking_pk>/no-show/",
        views.mark_no_show,
        name="mark_no_show",
    ),
]
