"""
Simple plotting script for visualizing simulation results
Generates separate graphs for each metric and overall comparison
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


def load_data(csv_file):
    """Load simulation data from CSV."""
    return pd.read_csv(csv_file)


def calculate_metrics(data):
    """Calculate energy and comfort metrics."""
    # Energy metrics - use component sum
    total_energy = (data['fan_power'].sum() + 
                   data['chiller_power'].sum() + 
                   data['pump_power'].sum()) / 1000
    
    # Comfort metrics
    min_comfort, max_comfort = 20.0, 26.0
    violations = ((data['zone_temp'] > max_comfort) | (data['zone_temp'] < min_comfort)).sum()
    compliance = (1 - violations / len(data)) * 100
    
    return {
        'total_energy_kwh': total_energy,
        'avg_zone_temp': data['zone_temp'].mean(),
        'max_zone_temp': data['zone_temp'].max(),
        'min_zone_temp': data['zone_temp'].min(),
        'avg_outdoor_temp': data['outdoor_temp'].mean(),
        'comfort_compliance': compliance,
        'total_fan_energy': data['fan_power'].sum() / 1000,
        'total_chiller_energy': data['chiller_power'].sum() / 1000,
        'total_pump_energy': data['pump_power'].sum() / 1000
    }


def plot_temperature_comparison(baseline_data, controlled_data, output_dir):
    """Plot temperature comparison."""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Zone temperature
    axes[0].plot(baseline_data['timestamp'], baseline_data['zone_temp'], 
                 label='Baseline', alpha=0.7, linewidth=0.5)
    axes[0].plot(controlled_data['timestamp'], controlled_data['zone_temp'], 
                 label='AI Controlled', alpha=0.7, linewidth=0.5)
    axes[0].axhline(y=20, color='r', linestyle='--', alpha=0.5, label='Min Comfort')
    axes[0].axhline(y=26, color='r', linestyle='--', alpha=0.5, label='Max Comfort')
    axes[0].set_ylabel('Zone Temperature (°C)')
    axes[0].set_title('Zone Temperature Comparison')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Outdoor temperature
    axes[1].plot(baseline_data['timestamp'], baseline_data['outdoor_temp'], 
                label='Outdoor', alpha=0.7, linewidth=0.5)
    axes[1].set_ylabel('Outdoor Temperature (°C)')
    axes[1].set_xlabel('Timestamp (hours)')
    axes[1].set_title('Outdoor Temperature')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'temperature_comparison.png', dpi=150)
    plt.close()
    print(f"[OK] Saved temperature_comparison.png")


def plot_energy_components(baseline_data, controlled_data, baseline_metrics, controlled_metrics, output_dir):
    """Plot energy component comparison."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Total energy comparison
    categories = ['Fan', 'Chiller', 'Pump', 'Total']
    baseline_vals = [baseline_metrics['total_fan_energy'], 
                     baseline_metrics['total_chiller_energy'],
                     baseline_metrics['total_pump_energy'],
                     baseline_metrics['total_energy_kwh']]
    controlled_vals = [controlled_metrics['total_fan_energy'], 
                       controlled_metrics['total_chiller_energy'],
                       controlled_metrics['total_pump_energy'],
                       controlled_metrics['total_energy_kwh']]
    
    x = np.arange(len(categories))
    width = 0.35
    
    axes[0, 0].bar(x - width/2, baseline_vals, width, label='Baseline', alpha=0.8)
    axes[0, 0].bar(x + width/2, controlled_vals, width, label='AI Controlled', alpha=0.8)
    axes[0, 0].set_ylabel('Energy (kWh)')
    axes[0, 0].set_title('Energy Component Comparison')
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(categories)
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    
    # Energy over time (cumulative)
    baseline_cumulative = (baseline_data['fan_power'] + 
                          baseline_data['chiller_power'] + 
                          baseline_data['pump_power']).cumsum() / 1000
    controlled_cumulative = (controlled_data['fan_power'] + 
                            controlled_data['chiller_power'] + 
                            controlled_data['pump_power']).cumsum() / 1000
    
    axes[0, 1].plot(baseline_data['timestamp'], baseline_cumulative, 
                   label='Baseline', alpha=0.7, linewidth=1)
    axes[0, 1].plot(controlled_data['timestamp'], controlled_cumulative, 
                   label='AI Controlled', alpha=0.7, linewidth=1)
    axes[0, 1].set_ylabel('Cumulative Energy (kWh)')
    axes[0, 1].set_xlabel('Timestamp (hours)')
    axes[0, 1].set_title('Cumulative Energy Consumption')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Fan power over time
    axes[1, 0].plot(baseline_data['timestamp'], baseline_data['fan_power'], 
                   label='Baseline', alpha=0.5, linewidth=0.5)
    axes[1, 0].plot(controlled_data['timestamp'], controlled_data['fan_power'], 
                   label='AI Controlled', alpha=0.5, linewidth=0.5)
    axes[1, 0].set_ylabel('Fan Power (W)')
    axes[1, 0].set_xlabel('Timestamp (hours)')
    axes[1, 0].set_title('Fan Power Consumption')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # Chiller power over time
    axes[1, 1].plot(baseline_data['timestamp'], baseline_data['chiller_power'], 
                   label='Baseline', alpha=0.5, linewidth=0.5)
    axes[1, 1].plot(controlled_data['timestamp'], controlled_data['chiller_power'], 
                   label='AI Controlled', alpha=0.5, linewidth=0.5)
    axes[1, 1].set_ylabel('Chiller Power (W)')
    axes[1, 1].set_xlabel('Timestamp (hours)')
    axes[1, 1].set_title('Chiller Power Consumption')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'energy_components.png', dpi=150)
    plt.close()
    print(f"[OK] Saved energy_components.png")


def plot_comfort_analysis(baseline_data, controlled_data, baseline_metrics, controlled_metrics, output_dir):
    """Plot comfort analysis."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Comfort compliance comparison
    categories = ['Baseline', 'AI Controlled']
    compliance_vals = [baseline_metrics['comfort_compliance'], controlled_metrics['comfort_compliance']]
    
    colors = ['lightcoral' if val < 90 else 'lightgreen' for val in compliance_vals]
    axes[0, 0].bar(categories, compliance_vals, color=colors, alpha=0.8)
    axes[0, 0].set_ylabel('Comfort Compliance (%)')
    axes[0, 0].set_title('Comfort Compliance Comparison')
    axes[0, 0].axhline(y=90, color='r', linestyle='--', alpha=0.5, label='Target (90%)')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    axes[0, 0].set_ylim(0, 100)
    
    # Temperature distribution
    axes[0, 1].hist(baseline_data['zone_temp'], bins=50, alpha=0.5, label='Baseline', density=True)
    axes[0, 1].hist(controlled_data['zone_temp'], bins=50, alpha=0.5, label='AI Controlled', density=True)
    axes[0, 1].axvline(x=20, color='r', linestyle='--', alpha=0.5, label='Min Comfort')
    axes[0, 1].axvline(x=26, color='r', linestyle='--', alpha=0.5, label='Max Comfort')
    axes[0, 1].set_xlabel('Zone Temperature (°C)')
    axes[0, 1].set_ylabel('Density')
    axes[0, 1].set_title('Temperature Distribution')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Temperature statistics
    stats_labels = ['Avg Temp', 'Max Temp', 'Min Temp']
    baseline_temps = [baseline_metrics['avg_zone_temp'], 
                      baseline_metrics['max_zone_temp'],
                      baseline_metrics['min_zone_temp']]
    controlled_temps = [controlled_metrics['avg_zone_temp'], 
                        controlled_metrics['max_zone_temp'],
                        controlled_metrics['min_zone_temp']]
    
    x = np.arange(len(stats_labels))
    width = 0.35
    
    axes[1, 0].bar(x - width/2, baseline_temps, width, label='Baseline', alpha=0.8)
    axes[1, 0].bar(x + width/2, controlled_temps, width, label='AI Controlled', alpha=0.8)
    axes[1, 0].set_ylabel('Temperature (°C)')
    axes[1, 0].set_title('Temperature Statistics')
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(stats_labels)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    axes[1, 0].axhline(y=20, color='r', linestyle='--', alpha=0.3)
    axes[1, 0].axhline(y=26, color='r', linestyle='--', alpha=0.3)
    
    # Comfort violations over time
    baseline_violations = ((baseline_data['zone_temp'] > 26) | (baseline_data['zone_temp'] < 20)).astype(int)
    controlled_violations = ((controlled_data['zone_temp'] > 26) | (controlled_data['zone_temp'] < 20)).astype(int)
    
    axes[1, 1].plot(baseline_data['timestamp'], baseline_violations, 
                   label='Baseline', alpha=0.5, linewidth=0.5)
    axes[1, 1].plot(controlled_data['timestamp'], controlled_violations, 
                   label='AI Controlled', alpha=0.5, linewidth=0.5)
    axes[1, 1].set_ylabel('Comfort Violation (1=Yes, 0=No)')
    axes[1, 1].set_xlabel('Timestamp (hours)')
    axes[1, 1].set_title('Comfort Violations Over Time')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'comfort_analysis.png', dpi=150)
    plt.close()
    print(f"[OK] Saved comfort_analysis.png")


def plot_overall_summary(baseline_metrics, controlled_metrics, output_dir):
    """Plot overall summary comparison."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Energy savings
    energy_savings = baseline_metrics['total_energy_kwh'] - controlled_metrics['total_energy_kwh']
    savings_percent = (energy_savings / baseline_metrics['total_energy_kwh']) * 100
    
    categories = ['Baseline', 'AI Controlled']
    energy_vals = [baseline_metrics['total_energy_kwh'], controlled_metrics['total_energy_kwh']]
    
    colors = ['lightcoral', 'lightgreen']
    bars = axes[0].bar(categories, energy_vals, color=colors, alpha=0.8)
    axes[0].set_ylabel('Total Energy (kWh)')
    axes[0].set_title(f'Total Energy Comparison\nSavings: {energy_savings:.2f} kWh ({savings_percent:.2f}%)')
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, val in zip(bars, energy_vals):
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.0f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # Key metrics comparison
    metrics = ['Energy (kWh)', 'Avg Temp (°C)', 'Comfort (%)']
    baseline_vals = [baseline_metrics['total_energy_kwh'], 
                     baseline_metrics['avg_zone_temp'],
                     baseline_metrics['comfort_compliance']]
    controlled_vals = [controlled_metrics['total_energy_kwh'], 
                       controlled_metrics['avg_zone_temp'],
                       controlled_metrics['comfort_compliance']]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    axes[1].bar(x - width/2, baseline_vals, width, label='Baseline', alpha=0.8)
    axes[1].bar(x + width/2, controlled_vals, width, label='AI Controlled', alpha=0.8)
    axes[1].set_ylabel('Value')
    axes[1].set_title('Key Metrics Comparison')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(metrics)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'overall_summary.png', dpi=150)
    plt.close()
    print(f"[OK] Saved overall_summary.png")


def main():
    """Main plotting function."""
    project_root = Path(__file__).parent
    output_dir = project_root / "output" / "plots"
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Eco-Loop Building Agents - Results Visualization")
    print("=" * 60)
    print()
    
    # Load data
    baseline_file = project_root / "output" / "baseline" / "simulation_data" / "simulation_data.csv"
    ai_file = project_root / "output" / "ai_controlled_basic" / "simulation_data" / "simulation_data.csv"
    
    if not baseline_file.exists():
        print(f"[ERROR] Baseline data not found: {baseline_file}")
        print("Run 'python main.py 1' to generate baseline data.")
        return
    
    if not ai_file.exists():
        print(f"[ERROR] AI control data not found: {ai_file}")
        print("Run 'python main.py 2' to generate AI control data.")
        return
    
    print("Loading simulation data...")
    baseline_data = load_data(baseline_file)
    controlled_data = load_data(ai_file)
    print(f"Baseline: {len(baseline_data)} data points")
    print(f"AI Controlled: {len(controlled_data)} data points")
    print()
    
    # Calculate metrics
    print("Calculating metrics...")
    baseline_metrics = calculate_metrics(baseline_data)
    controlled_metrics = calculate_metrics(controlled_data)
    
    print(f"\nBaseline Metrics:")
    print(f"  Total Energy: {baseline_metrics['total_energy_kwh']:.2f} kWh")
    print(f"  Avg Zone Temp: {baseline_metrics['avg_zone_temp']:.2f} °C")
    print(f"  Comfort Compliance: {baseline_metrics['comfort_compliance']:.2f}%")
    
    print(f"\nAI Controlled Metrics:")
    print(f"  Total Energy: {controlled_metrics['total_energy_kwh']:.2f} kWh")
    print(f"  Avg Zone Temp: {controlled_metrics['avg_zone_temp']:.2f} °C")
    print(f"  Comfort Compliance: {controlled_metrics['comfort_compliance']:.2f}%")
    
    energy_savings = baseline_metrics['total_energy_kwh'] - controlled_metrics['total_energy_kwh']
    savings_percent = (energy_savings / baseline_metrics['total_energy_kwh']) * 100
    print(f"\nEnergy Savings: {energy_savings:.2f} kWh ({savings_percent:.2f}%)")
    print()
    
    # Generate plots
    print("Generating plots...")
    plot_temperature_comparison(baseline_data, controlled_data, output_dir)
    plot_energy_components(baseline_data, controlled_data, baseline_metrics, controlled_metrics, output_dir)
    plot_comfort_analysis(baseline_data, controlled_data, baseline_metrics, controlled_metrics, output_dir)
    plot_overall_summary(baseline_metrics, controlled_metrics, output_dir)
    
    print()
    print("=" * 60)
    print("Plots saved to:", output_dir)
    print("=" * 60)


if __name__ == "__main__":
    main()
