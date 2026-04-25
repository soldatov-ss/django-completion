# django-completion

![PyPI version](https://img.shields.io/pypi/v/django-completion.svg)

Shell autocomplete and intelligent suggestions for Django's manage.py

* GitHub: https://github.com/soldatov-ss/django-completion/
* PyPI package: https://pypi.org/project/django-completion/
* Created by: **[Soldatov Serhii](https://github.com/soldatov-ss)** | GitHub https://github.com/soldatov-ss | PyPI https://pypi.org/user/soldatov-ss/
* Free software: MIT License

## Features

* TODO

## Documentation

Documentation is built with [Zensical](https://zensical.org/) and deployed to GitHub Pages.

* **Live site:** https://soldatov-ss.github.io/django_completion/
* **Preview locally:** `just docs-serve` (serves at http://localhost:8000)
* **Build:** `just docs-build`

API documentation is auto-generated from docstrings using [mkdocstrings](https://mkdocstrings.github.io/).

Docs deploy automatically on push to `main` via GitHub Actions. To enable this, go to your repo's Settings > Pages and set the source to **GitHub Actions**.

## Development

To set up for local development:

```bash
# Clone your fork
git clone git@github.com:your_username/django-completion.git
cd django-completion

# Install in editable mode with live updates
uv tool install --editable .
```

This installs the CLI globally but with live updates - any changes you make to the source code are immediately available when you run `django_completion`.

Run tests:

```bash
uv run pytest
```

Run quality checks (format, lint, type check, test):

```bash
just qa
```

## Author

django-completion was created in 2026 by Soldatov Serhii.

Built with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [audreyfeldroy/cookiecutter-pypackage](https://github.com/audreyfeldroy/cookiecutter-pypackage) project template.
