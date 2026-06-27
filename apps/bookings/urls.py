from django.urls import path

from apps.bookings import views

app_name = "bookings"

urlpatterns = [
    path("", views.client_calendar, name="client_calendar"),
    path("my/", views.my_bookings, name="my_bookings"),
    path("sessions/<int:pk>/book/", views.book_session, name="book_session"),
    path("bookings/<int:pk>/cancel/", views.cancel_booking, name="cancel_booking"),
]
