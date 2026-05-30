import os

import django
from django.test import Client, override_settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cutless_project.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.urls import get_resolver, reverse


User = get_user_model()


def ensure_test_user():
    user, _ = User.objects.get_or_create(
        username="tpl_check_user",
        defaults={"email": "tpl@test.com", "is_active": True},
    )
    user.set_password("test1234")
    user.is_active = True
    user.save()

    from usuarios.models import PerfilUsuario

    perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
    for field in PerfilUsuario._meta.fields:
        name = field.name
        if name.startswith("puede_") and isinstance(field.get_internal_type(), str):
            if field.get_internal_type() == "BooleanField":
                setattr(perfil, name, True)
    perfil.rol = "admin"
    perfil.save()
    return user


def collect_paths():
    paths = set()
    resolver = get_resolver()
    for name in resolver.reverse_dict:
        if not isinstance(name, str):
            continue
        if not (name.startswith("cutless:") or name.startswith("usuarios:")):
            continue
        try:
            paths.add((name, reverse(name)))
        except Exception:
            pass

    # common detail routes
    extras = [
        ("cutless:resultado", {"pk": 1}),
        ("cutless:editar_optimizacion", {"pk": 1}),
        ("cutless:detalle_proyecto", {"pk": 1}),
        ("cutless:detalle_presupuesto", {"pk": 1}),
        ("cutless:editar_material", {"pk": 1}),
        ("cutless:editar_cliente", {"pk": 1}),
        ("cutless:editar_proyecto", {"pk": 1}),
        ("cutless:editar_presupuesto", {"pk": 1}),
        ("cutless:editar_plantilla", {"pk": 1}),
        ("cutless:calcular_tiempo", {"pk": 1}),
        ("cutless:historial_cliente", {"pk": 1}),
        ("cutless:eliminar_material", {"pk": 1}),
        ("cutless:eliminar_cliente", {"pk": 1}),
        ("cutless:eliminar_proyecto", {"pk": 1}),
        ("cutless:eliminar_plantilla", {"pk": 1}),
        ("cutless:eliminar_optimizacion", {"pk": 1}),
        ("cutless:agregar_optimizaciones_proyecto", {"pk": 1}),
        ("cutless:agregar_optimizaciones_presupuesto", {"pk": 1}),
        ("usuarios:editar_usuario", {"pk": 1}),
    ]
    for name, kwargs in extras:
        try:
            paths.add((name, reverse(name, kwargs=kwargs)))
        except Exception:
            pass
    return sorted(paths, key=lambda x: x[1])


def main():
    user = ensure_test_user()
    client = Client()

    with override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"]):
        assert client.login(username=user.username, password="test1234")

        template_errors = []
        server_errors = []
        ok = 0

        for name, path in collect_paths():
            response = client.get(path)
            body = response.content.decode("utf-8", errors="ignore")
            if response.status_code >= 500:
                server_errors.append((name, path, response.status_code))
            elif "TemplateSyntaxError" in body or "Invalid block tag" in body:
                template_errors.append((name, path))
            elif response.status_code < 400:
                ok += 1

    print(f"OK responses: {ok}")
    print(f"Template errors: {len(template_errors)}")
    print(f"HTTP 5xx: {len(server_errors)}")

    for name, path in template_errors:
        print(f"  TPL  {name} -> {path}")
    for name, path, code in server_errors:
        print(f"  {code}  {name} -> {path}")

    if template_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
