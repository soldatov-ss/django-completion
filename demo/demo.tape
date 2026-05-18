# Run from the demo/ directory:
#   cd demo && vhs demo.tape
#
# Prerequisites:
#   1. vhs installed (https://github.com/charmbracelet/vhs)
#   2. django-completion installed: python manage.py autocomplete install --shell zsh

Output demo.gif

Set Shell "zsh"
Set FontSize 14
Set FontFamily "JetBrains Mono"
Set Width 860
Set Height 460
Set Theme "tokyonight"
Set Padding 24
Set TypingSpeed 40ms

Hide
Type "source ../.venv/bin/activate" Enter
Sleep 500ms
Type "autoload -Uz compinit && compinit -u 2>/dev/null" Enter
Sleep 800ms
Type "source ~/.local/share/django-completion/completion.zsh" Enter
Sleep 200ms
Type "python manage.py autocomplete refresh > /dev/null 2>&1" Enter
Sleep 3s
Type "LISTMAX=0" Enter
Type "PROMPT='$ '" Enter
Type "clear" Enter
Sleep 400ms
Show

Sleep 400ms

# Beat 1 — migrate app labels (local apps first, only apps with migrations)
Type "python manage.py migrate "
Tab
Sleep 2500ms
Ctrl+C

Hide
Type "clear" Enter
Sleep 200ms
Show

# Beat 2 — migration names for a specific app
Type "python manage.py migrate accounts "
Tab
Sleep 4500ms
Ctrl+C

Hide
Type "clear" Enter
Sleep 200ms
Show

# Beat 3 — option completion
Type "python manage.py runserver --"
Tab
Sleep 3000ms
