from argparse import ArgumentParser
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


def _detect_shell() -> Literal["zsh", "bash"]:
    """Infer the current shell from $SHELL, defaulting to bash."""
    shell = os.environ.get("SHELL", "")
    return "zsh" if "zsh" in shell else "bash"


def _script_content(shell: Literal["bash", "zsh"]) -> str:
    """Read the completion script template for the given shell."""
    tmpl = Path(__file__).parent.parent.parent / "scripts" / _TMPL_NAMES[shell]
    return tmpl.read_text()


def _source_block(script_path: Path) -> str:
    """Return a marker-delimited source line suitable for appending to an RC file."""
    return f"{_MARKER_BEGIN}\nsource {script_path}\n{_MARKER_END}\n"


def _is_installed(rc_path: Path) -> bool:
    """Return True if the completion block marker is present in rc_path."""
    try:
        return _MARKER_BEGIN in rc_path.read_text()
    except OSError:
        return False


class Command(BaseCommand):
    help = "Manage Django shell autocompletion"

    def add_arguments(self, parser: ArgumentParser) -> None:
        sub = parser.add_subparsers(dest="subcommand", metavar="subcommand")
        sub.required = True

        install = sub.add_parser("install", help="Install shell completion")
        install.add_argument("--shell", choices=["bash", "zsh"], help="Target shell (default: auto-detect)")

        sub.add_parser("status", help="Show completion status")
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
        script_path.write_text(_script_content(shell))

        rc_path = _SHELL_RC[shell]
        if _is_installed(rc_path):
            self.stdout.write(f"Completion already installed in {rc_path}")
            return

        with rc_path.open("a") as f:
            f.write(f"\n{_source_block(script_path)}")

        self.stdout.write(self.style.SUCCESS(f"Installed {shell} completion. Restart your shell or run:"))
        self.stdout.write(f"  source {rc_path}")

    def _status(self, options: dict[str, Any]) -> None:
        """Print cache age/staleness and per-shell installation status."""
        import time

        from django_completion.cache import COOLDOWN_SECONDS, _cache_path, is_stale, read_cache

        cache_path = _cache_path()
        cache = read_cache(cache_path)

        if cache is None:
            self.stdout.write("Cache: not found")
        else:
            age = int(time.time() - cache.get("generated_at", 0))
            stale = is_stale(cache, COOLDOWN_SECONDS)
            self.stdout.write(f"Cache: {cache_path} (age {age}s, {'stale' if stale else 'fresh'})")
            self.stdout.write(f"Commands: {len(cache.get('commands', []))}")
            self.stdout.write(f"Apps: {len(cache.get('app_labels', []))}")

        for shell, rc_path in _SHELL_RC.items():
            installed = _is_installed(rc_path)
            status = "installed" if installed else "not installed"
            self.stdout.write(f"{shell} hook: {status}")

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
            try:
                text = rc_path.read_text()
            except OSError:
                continue

            if _MARKER_BEGIN not in text:
                continue

            lines = text.splitlines(keepends=True)
            filtered = []
            inside = False
            for line in lines:
                if line.strip() == _MARKER_BEGIN:
                    inside = True
                elif line.strip() == _MARKER_END:
                    inside = False
                elif not inside:
                    filtered.append(line)

            rc_path.write_text("".join(filtered))
            self.stdout.write(self.style.SUCCESS(f"Removed {shell} completion from {rc_path}"))
