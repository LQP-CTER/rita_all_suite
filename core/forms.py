# File: Rita_All_Django/core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
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

class RegistrationForm(UserCreationForm):
    """
    Form đăng ký kế thừa từ UserCreationForm để đảm bảo an toàn,
    đồng thời thêm các trường tùy chỉnh và lưu vào Profile.
    """
    full_name = forms.CharField(
        label="Họ và tên",
        required=True,
        widget=forms.TextInput(attrs={'class': 'forms_field-input', 'placeholder': 'Họ và tên đầy đủ'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'forms_field-input', 'placeholder': 'Email'}),
        help_text='Bắt buộc. Vui lòng cung cấp một địa chỉ email hợp lệ.'
    )
    date_of_birth = forms.DateField(
        label="Ngày sinh",
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'forms_field-input'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'full_name', 'date_of_birth')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'forms_field-input', 'placeholder': 'Tên đăng nhập'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # UserCreationForm đã xử lý việc hash mật khẩu
        if commit:
            user.save()
            # Tạo hoặc cập nhật Profile sau khi User được tạo
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
    Form cập nhật thông tin cho cả User và Profile model.
    Kết hợp logic từ hai phiên bản và thêm styling.
    """
    username = forms.CharField(max_length=150, required=True, label="Tên đăng nhập", widget=forms.TextInput(attrs={'class': 'forms_field-input'}))
    email = forms.EmailField(required=True, label="Email", widget=forms.EmailInput(attrs={'class': 'forms_field-input'}))
    first_name = forms.CharField(max_length=30, required=False, label="Tên", widget=forms.TextInput(attrs={'class': 'forms_field-input'}))
    last_name = forms.CharField(max_length=150, required=False, label="Họ", widget=forms.TextInput(attrs={'class': 'forms_field-input'}))

    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'full_name', 'date_of_birth']
        labels = {
            'avatar': 'Ảnh đại diện',
            'bio': 'Tiểu sử',
            'full_name': 'Họ và tên đầy đủ',
            'date_of_birth': 'Ngày sinh'
        }
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'forms_field-input', 'rows': 3}),
            'avatar': forms.FileInput(attrs={'class': 'forms_field-input'}),
            'full_name': forms.TextInput(attrs={'class': 'forms_field-input'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'forms_field-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            # Lấy thông tin từ profile nếu có
            self.fields['full_name'].initial = self.instance.full_name
            self.fields['date_of_birth'].initial = self.instance.date_of_birth

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Email này đã được người khác sử dụng.")
        return email
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Tên đăng nhập này đã được người khác sử dụng.")
        return username

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.username = self.cleaned_data['username']
            self.user.email = self.cleaned_data['email']
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            if commit:
                self.user.save()
                profile.save()
        return profile