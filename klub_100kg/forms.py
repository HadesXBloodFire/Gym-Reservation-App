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
        trainers.insert(0, (None, 'Bez trenera'))  # Add an option for 'No trainer'
        return trainers

class ReservationForm(forms.Form):
    user_ID = forms.IntegerField(widget=forms.HiddenInput())  # This will be set in the view
    gym_ID = forms.ChoiceField(choices=get_gyms, label="Wybierz siłownię:")
    trainer_ID = forms.ChoiceField(choices=get_trainers, required=False, label="Wybierz trenera:")
    date = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M:%S.%fZ'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )