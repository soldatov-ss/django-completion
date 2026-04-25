import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

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


def _detect_shell() -> str:
    shell = os.environ.get("SHELL", "")
    return "zsh" if "zsh" in shell else "bash"


def _script_content(shell: str) -> str:
    tmpl = Path(__file__).parent.parent.parent / "scripts" / _TMPL_NAMES[shell]
    return tmpl.read_text()


def _source_block(script_path: Path) -> str:
    return f"{_MARKER_BEGIN}\nsource {script_path}\n{_MARKER_END}\n"


def _is_installed(rc_path: Path) -> bool:
    try:
        return _MARKER_BEGIN in rc_path.read_text()
    except OSError:
        return False


class Command(BaseCommand):
    help = "Manage Django shell autocompletion"

    def add_arguments(self, parser):
        sub = parser.add_subparsers(dest="subcommand", metavar="subcommand")
        sub.required = True

        install = sub.add_parser("install", help="Install shell completion")
        install.add_argument("--shell", choices=["bash", "zsh"], help="Target shell (default: auto-detect)")

        sub.add_parser("status", help="Show completion status")
        sub.add_parser("refresh", help="Force cache rebuild")
        sub.add_parser("uninstall", help="Remove shell completion")

    def handle(self, *args, **options):
        dispatch = {
            "install": self._install,
            "status": self._status,
            "refresh": self._refresh,
            "uninstall": self._uninstall,
        }
        dispatch[options["subcommand"]](options)

    def _install(self, options):
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

    def _status(self, options):
        from django_completion.cache import COOLDOWN_SECONDS, _cache_path, is_stale, read_cache
        import time

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

    def _refresh(self, options):
        from django_completion.cache import _cache_path, build_cache, write_cache

        data = build_cache()
        write_cache(data, _cache_path())
        self.stdout.write(self.style.SUCCESS(
            f"Cache rebuilt: {len(data['commands'])} commands, {len(data['app_labels'])} apps"
        ))

    def _uninstall(self, options):
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
