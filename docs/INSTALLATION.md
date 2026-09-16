# Installation & Lifecycle

## New computer

Prerequisites: Git and Python 3. GitHub CLI (`gh`) is convenient for cloning the private repository.

```bash
mkdir -p ~/Developer
cd ~/Developer
gh repo clone LucasLu3918/ai-product-system
cd ai-product-system
./scripts/bootstrap.sh
```

If `~/.local/bin` is not in PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then verify:

```bash
aips doctor
aips validate
aips version
```

## Initialize a project

```bash
aips init /path/to/project
```

This creates only the minimum `.ai/` workspace and records the system version/commit in `.ai/SYSTEM.yaml`.

## Before implementation

Every mutating AI implementation session begins with:

```bash
aips preflight /path/to/project
```

It updates only the AI Product System repository with `git pull --ff-only`, validates it, and records the exact version/commit used by the target project. It does **not** automatically pull the target project's Git repository.

The preflight stops when the system repo has local changes, is not on `main`, has divergent history, or a MAJOR version change requires explicit review.

After reviewing a major release:

```bash
aips preflight /path/to/project --allow-major
```

## Manual update

```bash
aips update
```

## Uninstall

Remove installed CLI/config and preserve the Git repository:

```bash
aips uninstall
```

Also remove the validation virtual environment:

```bash
aips uninstall --remove-venv
```

The repository is never deleted automatically.
