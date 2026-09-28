_cli_apply_python_environment() {
  local module="$1"
  local status
  shift

  local python="$HOME/.local/share/cli/venv/bin/python"
  local env_file="$HOME/.cliutils/source-env"

  if [[ ! -x "$python" ]]; then
    printf 'CLI Python environment not found: %s\n' "$python" >&2
    return 127
  fi

  if "$python" -m "$module" "$@"; then
    :
  else
    status=$?
    return "$status"
  fi

  if [[ -f "$env_file" ]]; then
    if . "$env_file"; then
      return 0
    else
      status=$?
      return "$status"
    fi
  fi
  return 0
}

java-v() {
  _cli_apply_python_environment cli.java_v "$@"
}

node-v() {
  _cli_apply_python_environment cli.node_v "$@"
}

python-v() {
  _cli_apply_python_environment cli.python_v "$@"
}
