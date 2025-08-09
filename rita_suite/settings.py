import os
from pathlib import Path
from dotenv import load_dotenv
<<<<<<< HEAD
=======
import dj_database_url # Thêm import mới
>>>>>>> a54cc739048d50b30967e31e8b0fbae68c1710e8

# Tải các biến từ file .env (chỉ dành cho môi trường development)
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Lấy SECRET_KEY từ biến môi trường
SECRET_KEY = os.environ.get('SECRET_KEY')

<<<<<<< HEAD
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# Lấy SECRET_KEY từ biến môi trường
SECRET_KEY = os.environ.get('SECRET_KEY')

# Lấy DEBUG từ biến môi trường. Mặc định là False cho production.
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# SỬA LỖI: Cấu hình để đọc tên miền được cho phép từ biến môi trường
ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS')
if ALLOWED_HOSTS_ENV:
    # Tách chuỗi thành một danh sách các tên miền, ví dụ: "domain1.com,domain2.com"
    ALLOWED_HOSTS = ALLOWED_HOSTS_ENV.split(',')
else:
    ALLOWED_HOSTS = []
=======
# Lấy DEBUG từ biến môi trường. Mặc định là False cho production.
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
>>>>>>> a54cc739048d50b30967e31e8b0fbae68c1710e8

# Cấu hình để đọc tên miền được cho phép từ biến môi trường
ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = ALLOWED_HOSTS_ENV.split(',')
else:
    ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rita_suite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
<<<<<<< HEAD
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Thêm thư mục templates gốc
=======
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
>>>>>>> a54cc739048d50b30967e31e8b0fbae68c1710e8
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rita_suite.wsgi.application'

<<<<<<< HEAD

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
=======
# --- CẤU HÌNH DATABASE MỚI ---
# Nếu có biến môi trường DATABASE_URL (trên Render), dùng Postgres.
# Nếu không, dùng SQLite cho môi trường local.
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
>>>>>>> a54cc739048d50b30967e31e8b0fbae68c1710e8
    }

# Password validation
<<<<<<< HEAD
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

=======
>>>>>>> a54cc739048d50b30967e31e8b0fbae68c1710e8
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
<<<<<<< HEAD
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'vi' # Đổi sang tiếng Việt

TIME_ZONE = 'Asia/Ho_Chi_Minh' # Đổi múi giờ Việt Nam

=======
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
>>>>>>> a54cc739048d50b30967e31e8b0fbae68c1710e8
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
<<<<<<< HEAD
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Thư mục Render sẽ dùng để thu thập file static
=======
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
>>>>>>> a54cc739048d50b30967e31e8b0fbae68c1710e8

# Media files (User uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
<<<<<<< HEAD
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
=======
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
>>>>>>> a54cc739048d50b30967e31e8b0fbae68c1710e8
