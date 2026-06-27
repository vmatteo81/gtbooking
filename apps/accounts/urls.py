from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.AccountsLoginView.as_view(), name="login"),
    path("logout/", views.AccountsLogoutView.as_view(), name="logout"),
    path("register/", views.register_client, name="register"),
    path("register/<slug:gym_slug>/", views.register_client, name="register_gym"),
]
