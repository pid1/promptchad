#!/usr/bin/env python3
"""
Promptchad - Web UI

Simple Flask server that wraps the CLI tool.
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import toml
from flask import Flask, jsonify, render_template, request

from promptchad import run_test

app = Flask(__name__)

CONFIG_PATH = Path("config.toml")
PROMPTS_DIR = Path("prompts")
LOGS_DIR = Path("logs")


def redact_api_key(key: str) -> str:
    """Redact API key, showing only last 4 characters."""
    if not key or len(key) <= 4:
        return "****"
    return f"****{key[-4:]}"


def get_config_for_logging(config: dict) -> dict:
    """Create a copy of config with redacted API keys for logging."""
    log_config = {"providers": {}}
    for provider, settings in config.get("providers", {}).items():
        log_config["providers"][provider] = {
            **settings,
            "api_key": redact_api_key(settings.get("api_key", ""))
        }
    return log_config


def log_test_run(prompt_a: str, prompt_b: str, shared_input: str, results_a: dict, results_b: dict, config: dict):
    """Log test run to a structured JSON Lines file."""
    LOGS_DIR.mkdir(exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "prompt_a": prompt_a,
            "prompt_b": prompt_b,
            "shared_input": shared_input,
        },
        "config": get_config_for_logging(config),
        "outputs": {
            "results_a": results_a,
            "results_b": results_b,
        }
    }
    
    # Append to daily log file
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


@app.route("/")
def index():
    """Serve the main UI."""
    return render_template("index.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    """Get current configuration."""
    if CONFIG_PATH.exists():
        config = toml.load(CONFIG_PATH)
        return jsonify(config)
    return jsonify({"providers": {}})


@app.route("/api/config", methods=["POST"])
def save_config():
    """Save configuration."""
    config = request.json
    with open(CONFIG_PATH, "w") as f:
        toml.dump(config, f)
    return jsonify({"success": True})


@app.route("/api/prompts", methods=["GET"])
def list_prompts():
    """List saved prompts."""
    PROMPTS_DIR.mkdir(exist_ok=True)
    prompts = [p.stem for p in PROMPTS_DIR.glob("*.txt")]
    return jsonify(prompts)


@app.route("/api/prompts/<name>", methods=["GET"])
def get_prompt(name):
    """Get a saved prompt."""
    prompt_path = PROMPTS_DIR / f"{name}.txt"
    if prompt_path.exists():
        return jsonify({"content": prompt_path.read_text()})
    return jsonify({"error": "Prompt not found"}), 404


@app.route("/api/prompts/<name>", methods=["POST"])
def save_prompt(name):
    """Save a prompt."""
    PROMPTS_DIR.mkdir(exist_ok=True)
    content = request.json.get("content", "")
    prompt_path = PROMPTS_DIR / f"{name}.txt"
    prompt_path.write_text(content)
    return jsonify({"success": True})


@app.route("/api/run", methods=["POST"])
def run():
    """Run the A/B prompt test."""
    data = request.json
    prompt_a = data.get("prompt_a", "").strip()
    prompt_b = data.get("prompt_b", "").strip()
    shared_input = data.get("shared_input", "").strip()
    
    if not prompt_a and not prompt_b:
        return jsonify({"error": "At least one prompt is required"}), 400
    
    if not CONFIG_PATH.exists():
        return jsonify({"error": "Config file not found"}), 400
    
    config = toml.load(CONFIG_PATH)
    
    # Combine prompts with shared input
    def combine_prompt(prompt, shared):
        if not prompt:
            return ""
        if not shared:
            return prompt
        return f"{prompt}\n\n---\n\n{shared}"
    
    full_prompt_a = combine_prompt(prompt_a, shared_input)
    full_prompt_b = combine_prompt(prompt_b, shared_input)
    
    # Run tests for both prompts
    results_a = asyncio.run(run_test(full_prompt_a, config)) if full_prompt_a else {}
    results_b = asyncio.run(run_test(full_prompt_b, config)) if full_prompt_b else {}
    
    # Log the test run (log original prompts and shared input separately)
    log_test_run(prompt_a, prompt_b, shared_input, results_a, results_b, config)
    
    return jsonify({
        "prompt_a": prompt_a,
        "prompt_b": prompt_b,
        "shared_input": shared_input,
        "results_a": results_a,
        "results_b": results_b,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
