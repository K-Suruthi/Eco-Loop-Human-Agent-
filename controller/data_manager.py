import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np


class DataManager:
    """Manages simulation data logging, storage, and analysis."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.data_history: List[Dict] = []
        self.control_actions_history: List[Dict] = []

        # Create data directory
        self.data_dir = self.output_dir / "simulation_data"
        self.data_dir.mkdir(exist_ok=True)

        # Initialize CSV file
        self.csv_file = self.data_dir / "simulation_data.csv"
        self._init_csv()

    def _init_csv(self):
        """Initialize CSV file with headers."""
        headers = [
            'timestamp',
            'zone_temp',
            'outdoor_temp',
            'fan_power',
            'chiller_power',
            'pump_power',
            'hvac_power',
            'cooling_rate',
            'heating_rate',
            'cooling_setpoint',
            'heating_setpoint'
        ]

        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def log_data(self, sensor_data: Dict, control_actions: Optional[Dict] = None):
        """Log sensor data and control actions to CSV and memory."""
        # Add control actions to sensor data if available
        log_entry = sensor_data.copy()
        if control_actions:
            log_entry['cooling_setpoint'] = control_actions.get('cooling_setpoint', None)
            log_entry['heating_setpoint'] = control_actions.get('heating_setpoint', None)
            self.control_actions_history.append({
                'timestamp': sensor_data['timestamp'],
                **control_actions
            })
        else:
            log_entry['cooling_setpoint'] = None
            log_entry['heating_setpoint'] = None

        # Store in memory
        self.data_history.append(log_entry)

        # Write to CSV
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                log_entry['timestamp'],
                log_entry['zone_temp'],
                log_entry['outdoor_temp'],
                log_entry['fan_power'],
                log_entry['chiller_power'],
                log_entry['pump_power'],
                log_entry['hvac_power'],
                log_entry['cooling_rate'],
                log_entry['heating_rate'],
                log_entry['cooling_setpoint'],
                log_entry['heating_setpoint']
            ])

    def get_summary_statistics(self) -> Dict:
        """Calculate summary statistics from collected data."""
        if not self.data_history:
            return {}

        data_array = np.array(self.data_history)

        # Calculate total HVAC energy as sum of components
        total_fan_energy = np.sum([d['fan_power'] for d in self.data_history]) / 1000
        total_chiller_energy = np.sum([d['chiller_power'] for d in self.data_history]) / 1000
        total_pump_energy = np.sum([d['pump_power'] for d in self.data_history]) / 1000
        total_hvac_energy = total_fan_energy + total_chiller_energy + total_pump_energy

        stats = {
            'total_hvac_energy_kwh': total_hvac_energy,
            'avg_zone_temp': np.mean([d['zone_temp'] for d in self.data_history]),
            'max_zone_temp': np.max([d['zone_temp'] for d in self.data_history]),
            'min_zone_temp': np.min([d['zone_temp'] for d in self.data_history]),
            'avg_outdoor_temp': np.mean([d['outdoor_temp'] for d in self.data_history]),
            'total_fan_energy_kwh': total_fan_energy,
            'total_chiller_energy_kwh': total_chiller_energy,
            'total_pump_energy_kwh': total_pump_energy,
            'num_data_points': len(self.data_history)
        }

        return stats

    def export_to_json(self, filename: str = "simulation_summary.json"):
        """Export summary statistics to JSON file."""
        stats = self.get_summary_statistics()
        output_file = self.data_dir / filename

        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)

        return output_file

    def load_baseline_data(self, baseline_file: Path) -> List[Dict]:
        """Load baseline simulation data for comparison."""
        baseline_data = []
        with open(baseline_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                baseline_data.append({
                    'timestamp': float(row['timestamp']),
                    'zone_temp': float(row['zone_temp']),
                    'outdoor_temp': float(row['outdoor_temp']),
                    'fan_power': float(row['fan_power']),
                    'chiller_power': float(row['chiller_power']),
                    'pump_power': float(row['pump_power']),
                    'hvac_power': float(row['hvac_power']),
                    'cooling_rate': float(row['cooling_rate']),
                    'heating_rate': float(row['heating_rate'])
                })

        return baseline_data

    def compare_with_baseline(self, baseline_data: List[Dict]) -> Dict:
        """Compare current simulation with baseline and calculate savings."""
        current_stats = self.get_summary_statistics()

        if not baseline_data:
            return {'error': 'No baseline data provided'}

        baseline_stats = {
            'total_hvac_energy_kwh': np.sum([d['hvac_power'] for d in baseline_data]) / 1000,
            'avg_zone_temp': np.mean([d['zone_temp'] for d in baseline_data]),
            'max_zone_temp': np.max([d['zone_temp'] for d in baseline_data]),
            'min_zone_temp': np.min([d['zone_temp'] for d in baseline_data])
        }

        comparison = {
            'baseline_energy_kwh': baseline_stats['total_hvac_energy_kwh'],
            'current_energy_kwh': current_stats['total_hvac_energy_kwh'],
            'energy_savings_kwh': baseline_stats['total_hvac_energy_kwh'] - current_stats['total_hvac_energy_kwh'],
            'energy_savings_percent': ((baseline_stats['total_hvac_energy_kwh'] - current_stats['total_hvac_energy_kwh']) / baseline_stats['total_hvac_energy_kwh']) * 100 if baseline_stats['total_hvac_energy_kwh'] > 0 else 0,
            'baseline_avg_temp': baseline_stats['avg_zone_temp'],
            'current_avg_temp': current_stats['avg_zone_temp'],
            'temp_diff': current_stats['avg_zone_temp'] - baseline_stats['avg_zone_temp']
        }

        return comparison

    def get_recent_data(self, num_points: int = 10) -> List[Dict]:
        """Get the most recent data points for real-time analysis."""
        return self.data_history[-num_points:] if len(self.data_history) >= num_points else self.data_history

    def clear_data(self):
        """Clear all stored data (useful for new simulations)."""
        self.data_history = []
        self.control_actions_history = []
        self._init_csv()
