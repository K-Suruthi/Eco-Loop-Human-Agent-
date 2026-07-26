"""
Eco-Loop Building Agents - Main Entry Point
AI-powered building energy optimization system
"""

import sys
import json
from pathlib import Path

ENERGYPLUS_PATH = r"C:\EnergyPlusV26-1-0"
sys.path.insert(0, ENERGYPLUS_PATH)

from controller.energyplus_runner import EnergyPlusRunner
from controller.ai_controller import AIController, EnhancedAIController
from analyzer import EnergyAnalyzer


def load_llm_config(project_root: Path) -> dict:
    """Load LLM configuration from file if exists."""
    config_file = project_root / "llm_config.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return None


def main():
    """Main execution function."""
    project_root = Path(__file__).parent

    print("=" * 60)
    print("Eco-Loop Building Agents")
    print("AI-Powered Building Energy Optimization")
    print("=" * 60)
    print()

    # Load LLM configuration
    llm_config = load_llm_config(project_root)
    if llm_config:
        print(f"[OK] LLM configuration loaded: {llm_config['provider']} ({llm_config['model']})")
    else:
        print("[INFO] No LLM configuration found. Run 'python setup_llm.py' to set up AI integration.")
        print("  AI control requires LLM configuration.")

    # Initialize runner
    runner = EnergyPlusRunner(project_root)

    # Get mode from command line argument or default to baseline
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print("\nAvailable simulation modes:")
        print("1. Baseline simulation (no control)")
        print("2. AI control (basic)")
        print("3. AI control (enhanced)")
        print("4. Run all and compare")
        print()
        print("Usage: python main.py [mode]")
        print("Example: python main.py 2")
        print("\nDefaulting to baseline simulation...")
        choice = "1"

    if choice == "1":
        # Baseline only
        print("\nRunning baseline simulation...")
        baseline_data = runner.run_baseline("baseline")
        print(f"Baseline energy: {baseline_data.get_summary_statistics()['total_hvac_energy_kwh']:.2f} kWh")

    elif choice == "2":
        # Basic AI control
        print("\nRunning AI-controlled simulation (basic)...")
        controller = AIController(project_root, use_ai=True, llm_config=llm_config)
        controlled_data = runner.run_controlled(controller, "ai_controlled_basic")
        print(f"Controlled energy: {controlled_data.get_summary_statistics()['total_hvac_energy_kwh']:.2f} kWh")

    elif choice == "3":
        # Enhanced AI control
        print("\nRunning AI-controlled simulation (enhanced)...")
        controller = EnhancedAIController(project_root, use_ai=True, llm_config=llm_config)
        controlled_data = runner.run_controlled(controller, "ai_controlled_enhanced")
        print(f"Controlled energy: {controlled_data.get_summary_statistics()['total_hvac_energy_kwh']:.2f} kWh")

    elif choice == "4":
        # Run all and compare
        print("\nRunning complete comparison...")

        # Baseline
        print("1. Running baseline...")
        baseline_data = runner.run_baseline("baseline")

        # AI control
        print("2. Running AI control (basic)...")
        ai_controller = AIController(project_root, use_ai=True, llm_config=llm_config)
        ai_data = runner.run_controlled(ai_controller, "ai_controlled_basic")

        # Analysis
        print("\n" + "=" * 60)
        print("COMPARISON RESULTS")
        print("=" * 60)

        analyzer = EnergyAnalyzer(project_root / "output")

        baseline_file = project_root / "output" / "baseline" / "simulation_data" / "simulation_data.csv"
        ai_file = project_root / "output" / "ai_controlled_basic" / "simulation_data" / "simulation_data.csv"

        if baseline_file.exists() and ai_file.exists():
            baseline_df = analyzer.load_simulation_data(baseline_file)
            ai_df = analyzer.load_simulation_data(ai_file)
            ai_comparison = analyzer.compare_simulations(baseline_df, ai_df)

            print("\nAI Control:")
            print(f"  Energy Savings: {ai_comparison['energy_comparison']['energy_savings_percent']:.2f}%")
            print(f"  Comfort Change: {ai_comparison['comfort_comparison']['comfort_change']:.2f}%")

        print("\nTo view detailed visualizations, run: python plot_results.py")

    else:
        print(f"Invalid choice: {choice}")
        print("Usage: python main.py [1-4]")
        print("1. Baseline simulation (no control)")
        print("2. AI control (basic)")
        print("3. AI control (enhanced)")
        print("4. Run all and compare")


if __name__ == "__main__":
    main()
