from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile

class LoginForm(AuthenticationForm):
    """
    Form đăng nhập tùy chỉnh để thêm các thuộc tính HTML cần thiết cho CSS.
    """
    username = forms.CharField(widget=forms.TextInput(
        attrs={
            'class': 'forms_field-input',
            'placeholder': 'Tên đăng nhập',
            'required': True
        }
    ))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'forms_field-input',
            'placeholder': 'Mật khẩu',
            'required': True
        }
    ))

class RegistrationForm(forms.ModelForm):
    """
    Form đăng ký được viết lại để khắc phục lỗi KeyError và đảm bảo hoạt động ổn định.
    """
    full_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'forms_field-input', 'placeholder': 'Họ và tên đầy đủ'})
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'forms_field-input'})
    )
    password = forms.CharField(
        label="Mật khẩu",
        widget=forms.PasswordInput(attrs={'class': 'forms_field-input', 'placeholder': 'Mật khẩu'})
    )
    password2 = forms.CharField(
        label="Xác nhận mật khẩu",
        widget=forms.PasswordInput(attrs={'class': 'forms_field-input', 'placeholder': 'Xác nhận mật khẩu'})
    )

    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'forms_field-input', 'placeholder': 'Tên đăng nhập'}),
            'email': forms.EmailInput(attrs={'class': 'forms_field-input', 'placeholder': 'Email'}),
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Mật khẩu xác nhận không khớp.')
        return cd['password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    'full_name': self.cleaned_data.get('full_name'),
                    'date_of_birth': self.cleaned_data.get('date_of_birth')
                }
            )
        return user

class ProfileUpdateForm(forms.ModelForm):
    """
    Form để người dùng cập nhật thông tin cá nhân.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'forms_field-input'})
    )

    class Meta:
        model = Profile
        fields = ['full_name', 'date_of_birth', 'bio', 'avatar']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'forms_field-input'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'forms_field-input'}),
            'bio': forms.Textarea(attrs={'class': 'forms_field-input', 'rows': 3}),
            'avatar': forms.FileInput(attrs={'class': 'forms_field-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Email này đã được người khác sử dụng.")
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.email = self.cleaned_data['email']
        if commit:
            self.user.save()
            profile.save()
        return profile
