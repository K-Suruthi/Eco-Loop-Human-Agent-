"""
LLM Setup Script for Eco-Loop Building Agents
Helps install and configure local open-source LLM via Ollama
"""

import subprocess
import sys
import json
from pathlib import Path
import platform


def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        return False
    print(f"[OK] Python version: {sys.version}")
    return True


def install_dependencies():
    """Install required Python packages."""
    print("\n=== Installing Python Dependencies ===")

    packages = [
        "aiohttp",
        "mcp"
    ]

    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"[OK] Installed {package}")
        except subprocess.CalledProcessError:
            print(f"[FAIL] Failed to install {package}")
            return False

    return True


def setup_ollama():
    """Set up Ollama for local LLM."""
    print("\n=== Setting up Ollama (Local LLM) ===")

    # Check if Ollama is already installed
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
        print(f"[OK] Ollama is already installed: {result.stdout.strip()}")
    except FileNotFoundError:
        print("Ollama is not installed on your system.")

        # Detect OS and provide installation instructions
        os_name = platform.system()
        if os_name == "Windows":
            print("\nTo install Ollama on Windows:")
            print("1. Download from: https://ollama.com/download")
            print("2. Run the installer")
            print("3. Restart your terminal")
        elif os_name == "Darwin":  # macOS
            print("\nTo install Ollama on macOS:")
            print("1. Download from: https://ollama.com/download")
            print("2. Run the installer")
            print("3. Restart your terminal")
        elif os_name == "Linux":
            print("\nTo install Ollama on Linux:")
            print("curl -fsSL https://ollama.com/install.sh | sh")

        response = input("\nHave you installed Ollama? (y/n): ").strip().lower()
        if response != 'y':
            print("Skipping Ollama setup")
            return False

    # Pull a model
    print("\nAvailable LLM models:")
    print("1. llama3 (Recommended, 4GB)")
    print("2. mistral (4GB)")
    print("3. qwen (4GB)")
    print("4. phi3 (2GB)")
    print("5. Skip model download")

    choice = input("Select model to download (1-5): ").strip()

    models = {
        "1": "llama3",
        "2": "mistral",
        "3": "qwen",
        "4": "phi3"
    }

    if choice in models:
        model = models[choice]
        print(f"\nDownloading {model} (this may take a while)...")
        try:
            subprocess.run(["ollama", "pull", model], check=True)
            print(f"[OK] Successfully downloaded {model}")
            return model
        except subprocess.CalledProcessError:
            print(f"[FAIL] Failed to download {model}")
            return None
    else:
        print("Skipping model download")
        return None


def create_config_file(config):
    """Create LLM configuration file."""
    config_path = Path(__file__).parent / "llm_config.json"

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"\n[OK] Configuration saved to: {config_path}")
    return config_path


def test_llm_connection(config):
    """Test LLM connection."""
    print("\n=== Testing LLM Connection ===")

    try:
        from llm_integration import create_llm_integration
        import asyncio

        llm = create_llm_integration(config)

        async def test():
            test_data = {
                'zone_temp': 24.0,
                'outdoor_temp': 25.0,
                'hvac_power': 3000,
                'timestamp': 36000
            }
            result = await llm.compute_control_actions(test_data)
            return result

        result = asyncio.run(test())

        if result:
            print("[OK] LLM connection successful!")
            print(f"  Cooling setpoint: {result.get('cooling_setpoint', 'N/A')}")
            print(f"  Heating setpoint: {result.get('heating_setpoint', 'N/A')}")
            print(f"  Reasoning: {result.get('reasoning', 'N/A')}")
            return True
        else:
            print("[FAIL] LLM connection failed")
            return False

    except Exception as e:
        print(f"[FAIL] LLM test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("Eco-Loop Building Agents - Open-Source LLM Setup")
    print("=" * 60)

    # Check Python version
    if not check_python_version():
        return

    # Install dependencies
    if not install_dependencies():
        print("\n[FAIL] Dependency installation failed")
        return

    # Set up Ollama
    model = setup_ollama()

    if model:
        config = {
            "provider": "ollama",
            "model": model,
            "ollama_host": "http://localhost:11434"
        }

        # Save configuration
        create_config_file(config)

        # Test connection
        test_llm_connection(config)

        print("\n" + "=" * 60)
        print("[OK] Open-Source LLM setup complete!")
        print("=" * 60)
        print("\nYou can now run the system with AI control:")
        print("  python main.py")
        print("\nSelect option 3 or 4 for AI-controlled simulation")
    else:
        print("\n[FAIL] LLM setup incomplete")
        print("Please install Ollama and download a model to use AI control")


if __name__ == "__main__":
    main()
