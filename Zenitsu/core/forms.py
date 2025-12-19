from django import forms 
from .models import UserInfo

class SignupForm(forms.ModelForm):
    class Meta:
        model = UserInfo
        fields = ['username','email', 'password']
