# Aryan Pawar Portfolio

A server-rendered personal portfolio built with Django 5.2. The `projects` app
provides public portfolio, resume, blog, and contact pages, plus a protected
content-management workspace and page-view analytics. The public interface uses
Django templates, custom CSS, and vanilla JavaScript.

## Local development

Requirements: Python 3.10 or newer and pip. Python 3.10 reached end of life;
use a currently security-supported Python version for deployment. Render is
pinned to Python 3.14.10.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DJANGO_DEBUG = "True"
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Uploaded project images and documents are stored
in the local `media/` directory. Run the tests with:

```powershell
python manage.py test
```

## Render deployment

The repository includes a Render web-service definition in `render.yaml` and
uses WhiteNoise for static assets. Configure these environment variables in
Render before deploying:

- `DJANGO_SECRET_KEY`: a randomly generated secret key (at least 50 characters).
- `DATABASE_URL`: the PostgreSQL connection URL.
- `DJANGO_EMAIL_USER` and `DJANGO_EMAIL_PASSWORD`: the SMTP account used for
  contact notifications. Existing services using the legacy `HOST_PASSWORD`
  variable remain supported.
- `DJANGO_SUPERUSER_PASSWORD`: a strong password for the configured workspace
  administrator.

The Render definition sets `DJANGO_DEBUG=False` and allows the service hostname
`portfolio-website.onrender.com`. If using a custom domain, add it to
`DJANGO_ALLOWED_HOSTS` as a comma-separated hostname list and set
`DJANGO_CSRF_TRUSTED_ORIGINS` to the corresponding comma-separated HTTPS
origins (for example, `https://portfolio.example.com`). Gunicorn binds to the
port assigned by Render. The build script collects static files, applies
database migrations, and creates the configured administrator only when that
account does not already exist. If any superuser setting is provided, all three
must be present. Build and migration failures are not suppressed.

### Uploaded media storage

Static assets are served by WhiteNoise, but uploaded project images and
documents use Django's filesystem storage. Render's default filesystem is
ephemeral, so uploads will not reliably survive deploys or restarts unless a
persistent disk or external object-storage backend is configured. To use a
Render disk, mount it and set `DJANGO_MEDIA_ROOT` to a directory on that disk;
do not point `DJANGO_MEDIA_ROOT` at the application directory. No paid disk or
third-party storage service is provisioned automatically.
