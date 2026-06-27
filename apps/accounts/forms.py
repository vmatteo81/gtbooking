from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from apps.accounts.models import UserProfile
from apps.gyms.models import Gym


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ClientRegistrationForm(UserCreationForm):
    gym = forms.ModelChoiceField(
        label="Palestra",
        queryset=Gym.objects.filter(is_active=True),
        required=True,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("gym",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "gym":
                field.widget.attrs.setdefault("class", "form-control")
        self.fields["gym"].widget.attrs.setdefault("class", "form-select")

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "role": UserProfile.Role.CLIENT,
                    "gym": self.cleaned_data["gym"],
                },
            )
        return user
