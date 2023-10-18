from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','email']

class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=30, label=_(u'First name'))
    last_name = forms.CharField(max_length=30, label=_(u'Last name'))
    username = forms.CharField(max_length=15, label=_(u'Username'))
    email = forms.EmailField(label=_(u'Email address'))
    password1 = forms.CharField(widget=forms.PasswordInput(render_value=False), label=_(u'Password'))
    password2 = forms.CharField(widget=forms.PasswordInput(render_value=False), label=_(u'Password (again)'))

    def clean(self):
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_(u'You must type the same password each time'))

        if User.objects.filter(username=self.cleaned_data.get('username')).count() > 0:
            raise ValidationError(_('There is already a user with the same username.'))

        if User.objects.filter(email=self.cleaned_data.get('email')).count() > 0:
            raise ValidationError(_('There is already a user with the same email address.'))

        return self.cleaned_data
    
    def save(self, profile_callback=None):
        new_user = User.objects.create_user(
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            email=self.cleaned_data['email']
            )
        new_user.save()
        return new_user