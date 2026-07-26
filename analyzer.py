import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns


class EnergyAnalyzer:
    """Analyzes simulation data to calculate energy savings and comfort metrics."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.plots_dir = output_dir / "plots"
        self.plots_dir.mkdir(exist_ok=True)

    def load_simulation_data(self, data_file: Path) -> pd.DataFrame:
        """Load simulation data from CSV file."""
        return pd.read_csv(data_file)

    def calculate_thermal_comfort(self, temp_data: pd.Series) -> Dict:
        """
        Calculate thermal comfort metrics based on ASHRAE Standard 55.
        Comfort range: 20-26°C during occupied hours.
        """
        min_comfort = 20.0
        max_comfort = 26.0

        # Calculate comfort violations
        too_hot = (temp_data > max_comfort).sum()
        too_cold = (temp_data < min_comfort).sum()
        total_points = len(temp_data)

        comfort_metrics = {
            'comfort_violations_hot': int(too_hot),
            'comfort_violations_cold': int(too_cold),
            'total_comfort_violations': int(too_hot + too_cold),
            'comfort_compliance_rate': (1 - (too_hot + too_cold) / total_points) * 100 if total_points > 0 else 0,
            'avg_temp': temp_data.mean(),
            'max_temp': temp_data.max(),
            'min_temp': temp_data.min(),
            'temp_std': temp_data.std()
        }

        return comfort_metrics

    def calculate_energy_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate energy consumption metrics."""
        # Convert power (W) to energy (kWh) assuming 1-hour time steps
        energy_metrics = {
            'total_hvac_energy_kwh': data['hvac_power'].sum() / 1000,
            'total_fan_energy_kwh': data['fan_power'].sum() / 1000,
            'total_chiller_energy_kwh': data['chiller_power'].sum() / 1000,
            'total_pump_energy_kwh': data['pump_power'].sum() / 1000,
            'avg_hvac_power_kw': data['hvac_power'].mean() / 1000,
            'peak_hvac_power_kw': data['hvac_power'].max() / 1000,
            'total_cooling_energy_kwh': data['cooling_rate'].sum() / 1000,
            'total_heating_energy_kwh': data['heating_rate'].sum() / 1000
        }

        return energy_metrics

    def compare_simulations(self, baseline_data: pd.DataFrame, controlled_data: pd.DataFrame) -> Dict:
        """Compare baseline and controlled simulations."""
        baseline_energy = self.calculate_energy_metrics(baseline_data)
        controlled_energy = self.calculate_energy_metrics(controlled_data)

        baseline_comfort = self.calculate_thermal_comfort(baseline_data['zone_temp'])
        controlled_comfort = self.calculate_thermal_comfort(controlled_data['zone_temp'])

        comparison = {
            'energy_comparison': {
                'baseline_total_kwh': baseline_energy['total_hvac_energy_kwh'],
                'controlled_total_kwh': controlled_energy['total_hvac_energy_kwh'],
                'energy_savings_kwh': baseline_energy['total_hvac_energy_kwh'] - controlled_energy['total_hvac_energy_kwh'],
                'energy_savings_percent': ((baseline_energy['total_hvac_energy_kwh'] - controlled_energy['total_hvac_energy_kwh']) / baseline_energy['total_hvac_energy_kwh']) * 100 if baseline_energy['total_hvac_energy_kwh'] > 0 else 0,
                'fan_savings_kwh': baseline_energy['total_fan_energy_kwh'] - controlled_energy['total_fan_energy_kwh'],
                'chiller_savings_kwh': baseline_energy['total_chiller_energy_kwh'] - controlled_energy['total_chiller_energy_kwh'],
                'pump_savings_kwh': baseline_energy['total_pump_energy_kwh'] - controlled_energy['total_pump_energy_kwh']
            },
            'comfort_comparison': {
                'baseline_compliance_rate': baseline_comfort['comfort_compliance_rate'],
                'controlled_compliance_rate': controlled_comfort['comfort_compliance_rate'],
                'comfort_change': controlled_comfort['comfort_compliance_rate'] - baseline_comfort['comfort_compliance_rate'],
                'baseline_avg_temp': baseline_comfort['avg_temp'],
                'controlled_avg_temp': controlled_comfort['avg_temp'],
                'temp_change': controlled_comfort['avg_temp'] - baseline_comfort['avg_temp']
            },
            'detailed_metrics': {
                'baseline': {**baseline_energy, **baseline_comfort},
                'controlled': {**controlled_energy, **controlled_comfort}
            }
        }

        return comparison

    def generate_comparison_plots(self, baseline_data: pd.DataFrame, controlled_data: pd.DataFrame):
        """Generate visualization plots comparing baseline and controlled simulations."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Plot 1: Zone Temperature Comparison
        axes[0, 0].plot(baseline_data['timestamp'], baseline_data['zone_temp'], label='Baseline', alpha=0.7)
        axes[0, 0].plot(controlled_data['timestamp'], controlled_data['zone_temp'], label='Controlled', alpha=0.7)
        axes[0, 0].axhline(y=20, color='r', linestyle='--', label='Min Comfort')
        axes[0, 0].axhline(y=26, color='r', linestyle='--', label='Max Comfort')
        axes[0, 0].set_xlabel('Time')
        axes[0, 0].set_ylabel('Zone Temperature (°C)')
        axes[0, 0].set_title('Zone Temperature Comparison')
        axes[0, 0].legend()
        axes[0, 0].grid(True)

        # Plot 2: HVAC Power Comparison
        axes[0, 1].plot(baseline_data['timestamp'], baseline_data['hvac_power'], label='Baseline', alpha=0.7)
        axes[0, 1].plot(controlled_data['timestamp'], controlled_data['hvac_power'], label='Controlled', alpha=0.7)
        axes[0, 1].set_xlabel('Time')
        axes[0, 1].set_ylabel('HVAC Power (W)')
        axes[0, 1].set_title('HVAC Power Consumption')
        axes[0, 1].legend()
        axes[0, 1].grid(True)

        # Plot 3: Cumulative Energy Comparison
        baseline_cumulative = np.cumsum(baseline_data['hvac_power']) / 1000
        controlled_cumulative = np.cumsum(controlled_data['hvac_power']) / 1000
        axes[1, 0].plot(baseline_data['timestamp'], baseline_cumulative, label='Baseline', alpha=0.7)
        axes[1, 0].plot(controlled_data['timestamp'], controlled_cumulative, label='Controlled', alpha=0.7)
        axes[1, 0].set_xlabel('Time')
        axes[1, 0].set_ylabel('Cumulative Energy (kWh)')
        axes[1, 0].set_title('Cumulative Energy Consumption')
        axes[1, 0].legend()
        axes[1, 0].grid(True)

        # Plot 4: Setpoint Changes (if available)
        if 'cooling_setpoint' in controlled_data.columns:
            axes[1, 1].plot(controlled_data['timestamp'], controlled_data['cooling_setpoint'], label='Cooling Setpoint', alpha=0.7)
            if 'heating_setpoint' in controlled_data.columns:
                axes[1, 1].plot(controlled_data['timestamp'], controlled_data['heating_setpoint'], label='Heating Setpoint', alpha=0.7)
            axes[1, 1].set_xlabel('Time')
            axes[1, 1].set_ylabel('Setpoint (°C)')
            axes[1, 1].set_title('Control Setpoints')
            axes[1, 1].legend()
            axes[1, 1].grid(True)
        else:
            axes[1, 1].text(0.5, 0.5, 'Setpoint data not available', ha='center', va='center')
            axes[1, 1].set_title('Control Setpoints')

        plt.tight_layout()
        plot_file = self.plots_dir / "comparison_plots.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        return plot_file

    def generate_summary_report(self, comparison: Dict) -> str:
        """Generate a text summary report."""
        report = []
        report.append("=" * 60)
        report.append("ENERGY SAVINGS ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")

        # Energy Savings
        report.append("ENERGY CONSUMPTION:")
        report.append(f"  Baseline Total: {comparison['energy_comparison']['baseline_total_kwh']:.2f} kWh")
        report.append(f"  Controlled Total: {comparison['energy_comparison']['controlled_total_kwh']:.2f} kWh")
        report.append(f"  Energy Savings: {comparison['energy_comparison']['energy_savings_kwh']:.2f} kWh")
        report.append(f"  Savings Percentage: {comparison['energy_comparison']['energy_savings_percent']:.2f}%")
        report.append("")

        # Component-wise savings
        report.append("COMPONENT SAVINGS:")
        report.append(f"  Fan: {comparison['energy_comparison']['fan_savings_kwh']:.2f} kWh")
        report.append(f"  Chiller: {comparison['energy_comparison']['chiller_savings_kwh']:.2f} kWh")
        report.append(f"  Pump: {comparison['energy_comparison']['pump_savings_kwh']:.2f} kWh")
        report.append("")

        # Thermal Comfort
        report.append("THERMAL COMFORT:")
        report.append(f"  Baseline Compliance: {comparison['comfort_comparison']['baseline_compliance_rate']:.2f}%")
        report.append(f"  Controlled Compliance: {comparison['comfort_comparison']['controlled_compliance_rate']:.2f}%")
        report.append(f"  Comfort Change: {comparison['comfort_comparison']['comfort_change']:.2f}%")
        report.append(f"  Baseline Avg Temp: {comparison['comfort_comparison']['baseline_avg_temp']:.2f} °C")
        report.append(f"  Controlled Avg Temp: {comparison['comfort_comparison']['controlled_avg_temp']:.2f} °C")
        report.append(f"  Temperature Change: {comparison['comfort_comparison']['temp_change']:.2f} °C")
        report.append("")

        report.append("=" * 60)

        return "\n".join(report)

    def save_analysis_results(self, comparison: Dict, filename: str = "analysis_results.json"):
        """Save analysis results to JSON file."""
        output_file = self.output_dir / filename
        with open(output_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        return output_file

    def run_full_analysis(self, baseline_file: Path, controlled_file: Path):
        """Run complete analysis pipeline."""
        # Load data
        baseline_data = self.load_simulation_data(baseline_file)
        controlled_data = self.load_simulation_data(controlled_file)

        # Compare simulations
        comparison = self.compare_simulations(baseline_data, controlled_data)

        # Generate plots
        plot_file = self.generate_comparison_plots(baseline_data, controlled_data)

        # Generate report
        report = self.generate_summary_report(comparison)

        # Save results
        json_file = self.save_analysis_results(comparison)

        # Save text report
        report_file = self.output_dir / "analysis_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)

        return {
            'comparison': comparison,
            'plot_file': plot_file,
            'json_file': json_file,
            'report_file': report_file,
            'report_text': report
        }
