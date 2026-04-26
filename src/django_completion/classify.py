from pathlib import Path
import site


def classify_app(app_config) -> str:
    """Return 'local' or 'pip' for an AppConfig."""
    try:
        module_file = app_config.module.__file__
    except AttributeError:
        return "pip"

    if not module_file:
        return "pip"

    module_path = Path(module_file).resolve()

    site_dirs = site.getsitepackages()
    user_site = site.getusersitepackages()
    if isinstance(user_site, str):
        site_dirs = [*site_dirs, user_site]

    for sp in site_dirs:
        try:
            module_path.relative_to(Path(sp).resolve())
            return "pip"
        except ValueError:
            continue

    try:
        from django.conf import settings

        if hasattr(settings, "BASE_DIR"):
            base_dir = Path(settings.BASE_DIR).resolve()
            try:
                module_path.relative_to(base_dir)
                return "local"
            except ValueError:
                pass
    except Exception:
        pass

    return "pip"
