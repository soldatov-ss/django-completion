from argparse import ArgumentParser
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
import os
from pathlib import Path
from typing import Any, Literal

from django.core.management.base import BaseCommand

_INSTALL_DIR = Path.home() / ".local" / "share" / "django-completion"
_MARKER_BEGIN = "# django-completion begin"
_MARKER_END = "# django-completion end"

_SHELL_RC = {
    "bash": Path.home() / ".bashrc",
    "zsh": Path.home() / ".zshrc",
}
_SCRIPT_NAMES = {
    "bash": "completion.bash",
    "zsh": "completion.zsh",
}
_TMPL_NAMES = {
    "bash": "bash_completion.sh.tmpl",
    "zsh": "zsh_completion.zsh.tmpl",
}

_SUPPORTED_SHELLS: tuple[Literal["bash", "zsh"], ...] = ("bash", "zsh")
_VERSION_PREFIX = "# django-completion version: "
_CURRENT_SCHEMA_VERSION = 2


def _detect_shell() -> Literal["zsh", "bash"]:
    """Infer the current shell from $SHELL, defaulting to bash."""
    shell = os.environ.get("SHELL", "")
    return "zsh" if "zsh" in shell else "bash"


def _script_content(shell: Literal["bash", "zsh"]) -> str:
    """Read the completion script template for the given shell."""
    tmpl = Path(__file__).parent.parent.parent / "scripts" / _TMPL_NAMES[shell]
    return tmpl.read_text()


def _package_version() -> str:
    """Return the installed package version, falling back to local project metadata."""
    try:
        return version("django-completion")
    except PackageNotFoundError:
        pass

    pyproject = Path(__file__).parents[4] / "pyproject.toml"
    in_project_table = False
    try:
        for line in pyproject.read_text().splitlines():
            stripped = line.strip()
            if stripped == "[project]":
                in_project_table = True
                continue
            if in_project_table and stripped.startswith("["):
                break
            if in_project_table and stripped.startswith("version"):
                _, raw_value = stripped.split("=", 1)
                return raw_value.strip().strip('"')
    except OSError:
        pass
    return "unknown"


def _versioned_script_content(shell: Literal["bash", "zsh"]) -> str:
    """Return script content with a version marker used by status diagnostics."""
    return f"{_VERSION_PREFIX}{_package_version()}\n{_script_content(shell)}"


def _source_block(script_path: Path) -> str:
    """Return a marker-delimited source line suitable for appending to an RC file."""
    return f"{_MARKER_BEGIN}\nsource {script_path}\n{_MARKER_END}\n"


def _is_installed(rc_path: Path) -> bool:
    """Return True if the completion block marker is present in rc_path."""
    try:
        return _MARKER_BEGIN in rc_path.read_text()
    except OSError:
        return False


def _remove_rc_block(rc_path: Path) -> bool:
    """Strip the marker-delimited block from rc_path; return True if anything was removed."""
    try:
        text = rc_path.read_text()
    except OSError:
        return False

    if _MARKER_BEGIN not in text:
        return False

    filtered = []
    inside = False
    for line in text.splitlines(keepends=True):
        if line.strip() == _MARKER_BEGIN:
            inside = True
        elif line.strip() == _MARKER_END:
            inside = False
        elif not inside:
            filtered.append(line)

    rc_path.write_text("".join(filtered))
    return True


def _script_version(script_path: Path) -> str | None:
    """Read the version marker from an installed script, if present."""
    try:
        first_line = script_path.read_text().splitlines()[0]
    except (OSError, IndexError):
        return None

    if not first_line.startswith(_VERSION_PREFIX):
        return None
    installed_version = first_line.removeprefix(_VERSION_PREFIX).strip()
    return installed_version or None


def _script_status(shell: Literal["bash", "zsh"], package_version: str) -> tuple[Path, str | None, str]:
    """Return the installed script path, parsed version, and human-readable status."""
    script_path = _INSTALL_DIR / _SCRIPT_NAMES[shell]
    if not script_path.exists():
        return script_path, None, "not installed"

    script_version = _script_version(script_path)
    if script_version == package_version:
        return script_path, script_version, "current"
    if script_version is None:
        return script_path, None, "outdated"
    return script_path, script_version, f"outdated (script v{script_version}, package v{package_version})"


def _schema_status(cache: dict[str, Any]) -> str:
    """Return a compact schema freshness label for the status summary.

    Caches without ``schema_version`` are treated as v1 caches. Any schema older
    than the current runtime schema is usable but reported as outdated so users
    know to run ``autocomplete refresh``.
    """
    schema_version = cache.get("schema_version")
    if isinstance(schema_version, int) and schema_version >= _CURRENT_SCHEMA_VERSION:
        return f"v{schema_version} (current)"
    if schema_version is None:
        return "v1 (outdated)"
    return f"v{schema_version} (outdated)"


def _generated_at_label(cache: dict[str, Any]) -> str:
    """Return the cache generation timestamp formatted for diagnostics."""
    generated_at = cache.get("generated_at")
    if isinstance(generated_at, int | float):
        return datetime.fromtimestamp(generated_at, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return "unknown"


def _migration_apps_label(cache: dict[str, Any]) -> str:
    """Return a verbose migration-app count with app names when available."""
    migrations = cache.get("migrations", {})
    migration_apps = sorted(migrations) if isinstance(migrations, dict) else []
    summary = str(len(migration_apps))
    if migration_apps:
        summary = f"{summary} ({', '.join(migration_apps)})"
    return summary


def _warning_count(cache: dict[str, Any]) -> int:
    """Return the number of cache warnings, ignoring malformed values."""
    warnings = cache.get("warnings", [])
    return len(warnings) if isinstance(warnings, list) else 0


class Command(BaseCommand):
    help = "Manage Django shell autocompletion"

    def add_arguments(self, parser: ArgumentParser) -> None:
        sub = parser.add_subparsers(dest="subcommand", metavar="subcommand")
        sub.required = True

        install = sub.add_parser("install", help="Install shell completion")
        install.add_argument("--shell", choices=["bash", "zsh"], help="Target shell (default: auto-detect)")

        status = sub.add_parser("status", help="Show completion status")
        status.add_argument("--verbose", action="store_true", help="Show full diagnostic details")

        sub.add_parser("refresh", help="Force cache rebuild")
        sub.add_parser("uninstall", help="Remove shell completion")

    def handle(self, *args: Any, **options: Any) -> None:
        dispatch = {
            "install": self._install,
            "status": self._status,
            "refresh": self._refresh,
            "uninstall": self._uninstall,
        }
        dispatch[options["subcommand"]](options)

    def _install(self, options: dict[str, Any]) -> None:
        """Write the completion script and append a source block to the shell RC file."""
        shell = options.get("shell") or _detect_shell()
        _INSTALL_DIR.mkdir(parents=True, exist_ok=True)

        script_path = _INSTALL_DIR / _SCRIPT_NAMES[shell]
        script_path.write_text(_versioned_script_content(shell))

        rc_path = _SHELL_RC[shell]
        if _is_installed(rc_path):
            self.stdout.write(f"Completion already installed in {rc_path}")
        else:
            with rc_path.open("a") as f:
                f.write(f"\n{_source_block(script_path)}")
            self.stdout.write(self.style.SUCCESS(f"Installed {shell} completion. Restart your shell or run:"))
            self.stdout.write(f"  source {rc_path}")

        from django_completion.cache import _cache_path, build_cache, write_cache

        data = build_cache()
        write_cache(data, _cache_path())
        self.stdout.write(
            self.style.SUCCESS(f"Cache built: {len(data['commands'])} commands, {len(data['app_labels'])} apps")
        )

    def _status(self, options: dict[str, Any]) -> None:
        """Print cache age/staleness and per-shell installation status."""
        import time

        from django_completion.cache import COOLDOWN_SECONDS, _cache_path, is_stale, read_cache

        cache_path = _cache_path()
        cache = read_cache(cache_path)
        package_version = _package_version()

        if options.get("verbose"):
            self._status_verbose(cache_path, cache, package_version)
            return

        if cache is None:
            self.stdout.write("Cache: not found")
        else:
            age = int(time.time() - cache.get("generated_at", 0))
            stale = is_stale(cache, COOLDOWN_SECONDS)
            self.stdout.write(f"Cache: {cache_path} (age {age}s, {'stale' if stale else 'fresh'})")
            self.stdout.write(f"Schema: {_schema_status(cache)}")
            self.stdout.write(f"Commands: {len(cache.get('commands', []))}")
            self.stdout.write(f"Apps: {len(cache.get('app_labels', []))}")
            self.stdout.write(f"Apps with migrations: {len(cache.get('migrations', {}))}")
            self.stdout.write(f"Warnings: {len(cache.get('warnings', []))}")

        for shell, rc_path in _SHELL_RC.items():
            installed = _is_installed(rc_path)
            status = "installed" if installed else "not installed"
            self.stdout.write(f"{shell} hook: {status}")

        for shell in _SUPPORTED_SHELLS:
            _, _, status = _script_status(shell, package_version)
            self.stdout.write(f"{shell} script: {status}")

    def _status_verbose(self, cache_path: Path, cache: dict[str, Any] | None, package_version: str) -> None:
        """Print full cache, hook, and script diagnostics."""
        self._write_verbose_cache_status(cache_path, cache)
        self._write_verbose_hook_status()
        self._write_verbose_script_status(package_version)
        self.stdout.write(f"Package version: {package_version}")

    def _write_verbose_cache_status(self, cache_path: Path, cache: dict[str, Any] | None) -> None:
        """Print cache-specific diagnostics for verbose status output."""
        if cache is None:
            self.stdout.write(f"Cache path: {cache_path} (not found)")
            self.stdout.write("Generated: never")
            self.stdout.write("Schema version: missing")
            self.stdout.write("Commands: 0")
            self.stdout.write("Apps: 0")
            self.stdout.write("Apps with migrations: 0")
            self.stdout.write("Warnings: 0")
            return

        # Verbose output favors explicit values over freshness labels so users
        # can paste it into bug reports without losing diagnostic detail.
        self.stdout.write(f"Cache path: {cache_path}")
        self.stdout.write(f"Generated: {_generated_at_label(cache)}")
        self.stdout.write(f"Schema version: {cache.get('schema_version', 1)}")
        self.stdout.write(f"Commands: {len(cache.get('commands', []))}")
        self.stdout.write(f"Apps: {len(cache.get('app_labels', []))}")
        self.stdout.write(f"Apps with migrations: {_migration_apps_label(cache)}")
        self.stdout.write(f"Warnings: {_warning_count(cache)}")

    def _write_verbose_hook_status(self) -> None:
        """Print shell RC hook diagnostics for verbose status output."""
        for shell, rc_path in _SHELL_RC.items():
            status = "installed" if _is_installed(rc_path) else "not installed"
            self.stdout.write(f"{shell} hook: {rc_path} ({status})")

    def _write_verbose_script_status(self, package_version: str) -> None:
        """Print installed script diagnostics for verbose status output."""
        for shell in _SUPPORTED_SHELLS:
            script_path, script_version, status = _script_status(shell, package_version)
            if status == "not installed":
                self.stdout.write(f"{shell} script: not installed")
                continue
            # The summary includes the package version for mismatches; verbose
            # output keeps just the script's version and currency at its path.
            version_label = f"v{script_version}" if script_version is not None else "unversioned"
            current_label = "current" if status == "current" else "outdated"
            self.stdout.write(f"{shell} script: {script_path} ({version_label}, {current_label})")

    def _refresh(self, options: dict[str, Any]) -> None:
        """Force a full cache rebuild and persist it to disk."""
        from django_completion.cache import _cache_path, build_cache, write_cache

        data = build_cache()
        write_cache(data, _cache_path())
        self.stdout.write(
            self.style.SUCCESS(f"Cache rebuilt: {len(data['commands'])} commands, {len(data['app_labels'])} apps")
        )

    def _uninstall(self, options: dict[str, Any]) -> None:
        """Remove the marker-delimited completion block from all shell RC files."""
        for shell, rc_path in _SHELL_RC.items():
            if _remove_rc_block(rc_path):
                self.stdout.write(self.style.SUCCESS(f"Removed {shell} completion from {rc_path}"))

        for script_name in _SCRIPT_NAMES.values():
            script_path = _INSTALL_DIR / script_name
            try:
                script_path.unlink()
                self.stdout.write(self.style.SUCCESS(f"Deleted {script_path}"))
            except FileNotFoundError:
                pass

        try:
            _INSTALL_DIR.rmdir()
            self.stdout.write(self.style.SUCCESS(f"Removed {_INSTALL_DIR}"))
        except (FileNotFoundError, OSError):
            pass
