#!/usr/bin/env python3
"""
Promptchad - CLI

Test prompts across multiple AI providers and compare results.
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

import toml


async def call_openai(prompt: str, config: dict) -> dict:
    """Call OpenAI API."""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=config["api_key"])
        start_time = time.time()
        
        response = await client.chat.completions.create(
            model=config.get("model", "gpt-5.2"),
            messages=[{"role": "user", "content": prompt}],
            temperature=config.get("temperature", 0.7),
            max_completion_tokens=config.get("max_tokens", 1024),
        )
        
        elapsed = time.time() - start_time
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "elapsed_seconds": round(elapsed, 2),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def call_anthropic(prompt: str, config: dict) -> dict:
    """Call Anthropic API."""
    try:
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=config["api_key"])
        start_time = time.time()
        
        response = await client.messages.create(
            model=config.get("model", "claude-3-5-sonnet-20241022"),
            max_tokens=config.get("max_tokens", 1024),
            messages=[{"role": "user", "content": prompt}],
        )
        
        elapsed = time.time() - start_time
        return {
            "success": True,
            "response": response.content[0].text,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "elapsed_seconds": round(elapsed, 2),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def call_google(prompt: str, config: dict) -> dict:
    """Call Google Gemini API."""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=config["api_key"])
        model = genai.GenerativeModel(config.get("model", "gemini-pro"))
        
        start_time = time.time()
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=config.get("temperature", 0.7),
                max_output_tokens=config.get("max_tokens", 1024),
            ),
        )
        
        elapsed = time.time() - start_time
        return {
            "success": True,
            "response": response.text,
            "model": config.get("model", "gemini-pro"),
            "elapsed_seconds": round(elapsed, 2),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Provider registry
PROVIDERS = {
    "openai": call_openai,
    "anthropic": call_anthropic,
    "google": call_google,
}


async def run_test(prompt: str, config: dict) -> dict:
    """Run the prompt against all enabled providers."""
    results = {}
    tasks = []
    provider_names = []
    
    providers_config = config.get("providers", {})
    
    for provider_name, provider_config in providers_config.items():
        if not provider_config.get("enabled", True):
            continue
        
        if provider_name not in PROVIDERS:
            results[provider_name] = {
                "success": False,
                "error": f"Unknown provider: {provider_name}",
            }
            continue
        
        if not provider_config.get("api_key"):
            results[provider_name] = {
                "success": False,
                "error": "API key not configured",
            }
            continue
        
        provider_names.append(provider_name)
        tasks.append(PROVIDERS[provider_name](prompt, provider_config))
    
    if tasks:
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for name, response in zip(provider_names, responses):
            if isinstance(response, Exception):
                results[name] = {"success": False, "error": str(response)}
            else:
                results[name] = response
    
    return results


def load_config(config_path: Path) -> dict:
    """Load configuration from TOML file."""
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    
    return toml.load(config_path)


def load_prompt(prompt_path: Path) -> str:
    """Load prompt from file."""
    if not prompt_path.exists():
        print(f"Error: Prompt file not found: {prompt_path}", file=sys.stderr)
        sys.exit(1)
    
    return prompt_path.read_text()


def format_text_output(results: dict, prompt: str) -> str:
    """Format results as human-readable text."""
    lines = []
    lines.append("=" * 80)
    lines.append("PROMPT A/B TEST RESULTS")
    lines.append("=" * 80)
    lines.append("")
    lines.append("PROMPT:")
    lines.append("-" * 40)
    lines.append(prompt[:500] + ("..." if len(prompt) > 500 else ""))
    lines.append("")
    
    for provider, result in results.items():
        lines.append("=" * 80)
        lines.append(f"PROVIDER: {provider.upper()}")
        lines.append("-" * 40)
        
        if result.get("success"):
            if result.get("model"):
                lines.append(f"Model: {result['model']}")
            if result.get("elapsed_seconds"):
                lines.append(f"Time: {result['elapsed_seconds']}s")
            if result.get("usage"):
                usage = result["usage"]
                usage_str = ", ".join(f"{k}: {v}" for k, v in usage.items())
                lines.append(f"Usage: {usage_str}")
            lines.append("")
            lines.append("RESPONSE:")
            lines.append(result["response"])
        else:
            lines.append(f"ERROR: {result.get('error', 'Unknown error')}")
        
        lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Test prompts across multiple AI providers"
    )
    parser.add_argument(
        "prompt_file",
        type=Path,
        help="Path to the prompt file",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path("config.toml"),
        help="Path to config file (default: config.toml)",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--prompt-text",
        "-p",
        type=str,
        help="Use this text as prompt instead of reading from file",
    )
    
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    if args.prompt_text:
        prompt = args.prompt_text
    else:
        prompt = load_prompt(args.prompt_file)
    
    results = asyncio.run(run_test(prompt, config))
    
    if args.output == "json":
        output = {
            "prompt": prompt,
            "results": results,
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_text_output(results, prompt))


if __name__ == "__main__":
    main()
