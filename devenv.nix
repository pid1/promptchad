{ pkgs, lib, config, inputs, ... }:

{
  # Python 3.13 with uv
  languages.python = {
    enable = true;
    version = "3.13";
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  # Packages available in the shell
  packages = with pkgs; [
    # Add any additional system packages here
  ];

  # Environment variables
  env = {
    PYTHONDONTWRITEBYTECODE = "1";
  };

  # Scripts/commands available in the shell
  scripts = {
    dev.exec = ''
      if [ ! -f config.toml ]; then
        echo "Creating config.toml from example..."
        cp config.toml.example config.toml
        echo "⚠️  Add your API keys to config.toml before running tests"
        echo ""
      fi
      echo "Installing dependencies..."
      uv sync
      echo ""
      echo "Starting web UI at http://localhost:5000"
      uv run python web_ui.py
    '';

    cli.exec = ''
      uv run python promptchad.py "$@"
    '';

    test-prompt.exec = ''
      uv run python promptchad.py prompts/sample.txt "$@"
    '';
  };

  # Pre-commit hooks (optional)
  # pre-commit.hooks = {
  #   ruff.enable = true;
  # };

  enterShell = ''
    echo ""
    echo "🧪 Promptchad"
    echo ""
    echo "Commands:"
    echo "  dev          - Start the web UI server"
    echo "  cli <file>   - Run CLI with a prompt file"
    echo "  test-prompt  - Test with the sample prompt"
    echo ""
    echo "First time? Add your API keys to config.toml"
    echo ""
  '';
}
