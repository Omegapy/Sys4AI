#!/bin/zsh
# Resolve the selected project from this launcher, including paths with spaces.
set -eu
project_root="${0:A:h}"
setup="$project_root/Project App Setup.html"
show_setup() {
  if [[ -f "$setup" && ! -L "$setup" ]]; then
    /usr/bin/open "$setup"
  else
    /usr/bin/osascript -e 'display alert "Project app setup is incomplete" message "Ask your project maintainer to restore Project App Setup.html and the reviewed Project app package."' >/dev/null 2>&1 || true
  fi
}
package="$project_root/.agents/skills/ontology/scripts/project_app.py"
if [[ ! -f "$package" || -L "$package" ]]; then
  show_setup
  exit 1
fi
# Select a prepared interpreter only. No package install, build, or environment activation.
python_runtime=""
for candidate in "$project_root/.venv/bin/python" /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12 /usr/bin/python3; do
  [[ -x "$candidate" ]] || continue
  runtime_kind="$(/usr/bin/file -Lb -- "$candidate")"
  [[ "$runtime_kind" == *Mach-O* ]] || continue
  if "$candidate" -I -S -B -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3,12) else 1)' >/dev/null 2>&1; then
    python_runtime="$candidate"
    break
  fi
done
if [[ -z "$python_runtime" ]]; then
  show_setup
  exit 1
fi
if ! "$python_runtime" -I -S -B "$package" --project-root "$project_root" --open; then
  show_setup
  exit 1
fi
