import sys
from pathlib import Path
from typing import Optional

ENERGYPLUS_PATH = r"C:\EnergyPlusV26-1-0"
sys.path.insert(0, ENERGYPLUS_PATH)

from pyenergyplus.api import EnergyPlusAPI
from .callbacks import BuildingCallbacks
from .data_manager import DataManager


class EnergyPlusRunner:
    """Manages EnergyPlus simulation execution with different control modes."""

    def __init__(self, project_root: Path):
        self.api = EnergyPlusAPI()
        self.project_root = project_root
        self.state = None

        # File paths
        self.idf = project_root / "idf" / "5ZoneAirCooled.idf"
        self.weather = project_root / "weather" / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw"
        self.output_dir = project_root / "output"

    def run_baseline(self, output_subdir: str = "baseline", simulation_period: str = None) -> DataManager:
        """Run baseline simulation without any control (default setpoints).
        
        Args:
            output_subdir: Output directory name
            simulation_period: Simulation period (e.g., "1/1 to 1/7" for 1 week, "1/1 to 1/31" for 1 month)
                           If None, runs full year simulation
        """
        print("\n=== Running Baseline Simulation ===")
        if simulation_period:
            print(f"Simulation period: {simulation_period}")

        # Create specific output directory
        output_path = self.output_dir / output_subdir
        data_manager = DataManager(output_path)

        # Initialize state
        self.state = self.api.state_manager.new_state()

        # Create callbacks with data logger only (no controller)
        callbacks = BuildingCallbacks(data_logger=data_manager, controller=None)

        # Register callback
        self.api.runtime.callback_after_predictor_after_hvac_managers(
            self.state,
            callbacks.callback
        )

        # Build simulation arguments
        args = [
            "-w",
            str(self.weather),
            "-d",
            str(output_path),
            str(self.idf),
        ]

        # Add simulation period if specified
        if simulation_period:
            args.extend(["-p", simulation_period])

        # Run simulation
        self.api.runtime.run_energyplus(
            self.state,
            args,
        )

        # Export summary
        summary_file = data_manager.export_to_json("baseline_summary.json")
        print(f"\nBaseline simulation complete. Summary saved to: {summary_file}")

        return data_manager

    def run_controlled(self, controller, output_subdir: str = "controlled", simulation_period: str = None) -> DataManager:
        """Run simulation with rule-based or AI controller.
        
        Args:
            controller: Controller instance (AI or rule-based)
            output_subdir: Output directory name
            simulation_period: Simulation period (e.g., "1/1 to 1/7" for 1 week, "1/1 to 1/31" for 1 month)
                           If None, runs full year simulation
        """
        print(f"\n=== Running Controlled Simulation ({controller.__class__.__name__}) ===")
        if simulation_period:
            print(f"Simulation period: {simulation_period}")

        # Create specific output directory
        output_path = self.output_dir / output_subdir
        data_manager = DataManager(output_path)

        # Initialize state
        self.state = self.api.state_manager.new_state()

        # Create callbacks with data logger and controller
        callbacks = BuildingCallbacks(data_logger=data_manager, controller=controller)

        # Register callback
        self.api.runtime.callback_after_predictor_after_hvac_managers(
            self.state,
            callbacks.callback
        )

        # Build simulation arguments
        args = [
            "-w",
            str(self.weather),
            "-d",
            str(output_path),
            str(self.idf),
        ]

        # Add simulation period if specified
        if simulation_period:
            args.extend(["-p", simulation_period])

        # Run simulation
        self.api.runtime.run_energyplus(
            self.state,
            args,
        )

        # Export summary
        summary_file = data_manager.export_to_json("controlled_summary.json")
        print(f"\nControlled simulation complete. Summary saved to: {summary_file}")

        return data_manager


def main():
    """Main execution function for testing."""
    project_root = Path(__file__).parent.parent

    print("IDF:", project_root / "idf" / "5ZoneAirCooled.idf")
    print("Weather:", project_root / "weather" / "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")
    print("Output:", project_root / "output")

    runner = EnergyPlusRunner(project_root)

    # Run baseline simulation
    baseline_data = runner.run_baseline("baseline")

    print("\nUse main.py to run controlled simulations with AI controller.")


if __name__ == "__main__":
    main()