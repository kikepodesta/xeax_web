# Project context

- Django app: `main_app`; templates: `main_app/templates/main_app`; shared styles: `assets/css/custom.css`.
- Use `venv/bin/python manage.py check` for Django system checks and `git diff --check` for whitespace checks.
- Tests live in `main_app/tests.py`. The normal settings use PostgreSQL. For an isolated SQLite smoke test without touching the configured database or editing settings:

```sh
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xeax_sports_project.settings'); from django.conf import settings; settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}; import django; django.setup(); from django.test.runner import DiscoverRunner; raise SystemExit(bool(DiscoverRunner(verbosity=1).run_tests(['main_app'])))"
```

- Product content is translated through `ProductTranslation`; images use `ProductImage.order` and `id`. The first image is the main image. Active variants control purchase availability.
- Preserve the featured-product grid alongside the home slider. Product pages should use actual product content, display listing/A+ images without cropping, and support more than seven images.
