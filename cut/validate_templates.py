"""Validate Django template syntax for all project templates."""
import os
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cutless_project.settings")
django.setup()

from django.template import TemplateSyntaxError
from django.template.loader import get_template

BASE = Path(__file__).resolve().parent
TEMPLATE_DIRS = [
    BASE / "cutless" / "templates",
    BASE / "usuarios" / "templates",
]

failed = []
ok = []

for template_dir in TEMPLATE_DIRS:
    for path in sorted(template_dir.rglob("*.html")):
        rel = path.relative_to(template_dir).as_posix()
        try:
            get_template(rel)
            ok.append(rel)
        except TemplateSyntaxError as exc:
            failed.append((rel, str(exc)))
        except Exception as exc:
            failed.append((rel, f"{type(exc).__name__}: {exc}"))

print(f"OK: {len(ok)}")
print(f"FAIL: {len(failed)}")
for name, err in failed:
    print("---")
    print(name)
    print(err)

if failed:
    raise SystemExit(1)
