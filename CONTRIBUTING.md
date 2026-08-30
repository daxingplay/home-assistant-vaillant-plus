# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## Development environment

Home Assistant 2024.2 is the oldest release this integration supports, and it
needs Python 3.11 or newer; the most recent releases need 3.14. If your system
Python is older than that, `scripts/setup` installs a suitable interpreter with
[uv](https://docs.astral.sh/uv/) — no root required — and creates a `.venv`
with the test dependencies:

```bash
scripts/setup
.venv/bin/python -m pytest
```

To reproduce a specific entry of the CI matrix, pick the Python that Home
Assistant release supports and pin the matching
`pytest-homeassistant-custom-component`:

```bash
PYTHON_VERSION=3.13 PHCC_VERSION=0.13.272 scripts/setup  # Home Assistant 2025.8.3
.venv/bin/python -m pytest
```

Each entry in `.github/workflows/actions.yml` names the Home Assistant version
it pins, so the two values can be read straight off the matrix.

## Github is used for everything

Github is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `master`.
2. If you've changed something, update the documentation.
3. Make sure your code lints (using black).
4. Test you contribution.
5. Issue that pull request!

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](../../issues)

GitHub issues are used to track public bugs.
Report a bug by [opening a new issue](../../issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## Use a Consistent Coding Style

Use [black](https://github.com/ambv/black) to make sure the code follows the style.

## Test your code modification

This custom component is based on [integration_blueprint template](https://github.com/custom-components/integration_blueprint).

It comes with development environment in a container, easy to launch
if you use Visual Studio Code. With this container you will have a stand alone
Home Assistant instance running and already configured with the included
[`.devcontainer/configuration.yaml`](./.devcontainer/configuration.yaml)
file.

Run tests using `pytest`, if no working, use `python -m pytest`.

## Sign your commits

If you have issues when signing your commits with an error `fatal: cannot run /usr/local/bin/gpg: No such file or directory`, run the following command in your devcontainer terminal:
```
git config --global gpg.program $(which gpg)
```

## License

By contributing, you agree that your contributions will be licensed under its GPLv3 License.
