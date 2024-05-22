# klub_100kg/forms.py
from django import forms
from django.db import connection
class LoginForm(forms.Form):
    mail = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    mail = forms.EmailField()
    phone_number = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

def get_gyms():
    with connection.cursor() as cursor:
        cursor.execute("SELECT gym_ID, name FROM gyms")
        return cursor.fetchall()

def get_trainers():
    with connection.cursor() as cursor:
        cursor.execute("SELECT trainer_ID, first_name FROM trainers")
        trainers = cursor.fetchall()
        trainers.insert(0, (0, 'Bez trenera'))
        return trainers

class ReservationForm(forms.Form):
    user_ID = forms.IntegerField(widget=forms.HiddenInput())
    gym_ID = forms.ChoiceField(choices=get_gyms, label="Wybierz siłownię:")
    trainer_ID = forms.ChoiceField(choices=get_trainers, required=False, label="Wybierz trenera:")
    date = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M:%S.%fZ'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )

    def clean_trainer_ID(self):
        trainer_id = self.cleaned_data.get('trainer_ID')
        return 0 if trainer_id == '0' else trainer_id

class ModifyReservationForm(forms.Form):
    reservation_id = forms.IntegerField(widget=forms.HiddenInput())
    trainer_ID = forms.ChoiceField(choices=[], required=False, label="Wybierz trenera:")

    def __init__(self, *args, **kwargs):
        super(ModifyReservationForm, self).__init__(*args, **kwargs)
        self.fields['trainer_ID'].choices = get_trainers()
