"""
Live Monitoring Dashboard for Real-Time Simulation Metrics
Displays energy savings, temperature, and other metrics as simulation runs
"""
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
from pathlib import Path
import numpy as np


class LiveDashboard:
    """Live monitoring dashboard for simulation metrics."""
    
    def __init__(self, baseline_file, controlled_file, update_interval=2):
        self.baseline_file = baseline_file
        self.controlled_file = controlled_file
        self.update_interval = update_interval
        
        # Initialize data
        self.baseline_data = pd.DataFrame()
        self.controlled_data = pd.DataFrame()
        
        # Setup figure with better styling
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.ion()  # Interactive mode
        
        # Create figure with better layout
        self.fig = plt.figure(figsize=(16, 14))
        self.fig.patch.set_facecolor('#f0f0f0')
        self.fig.suptitle('Live AI Building Control Dashboard', fontsize=18, fontweight='bold', 
                          color='#2c3e50', y=0.97)
        
        # Create subplots with better spacing to prevent overlap
        gs = self.fig.add_gridspec(4, 2, hspace=0.4, wspace=0.3, top=0.91, bottom=0.06, left=0.07, right=0.96)
        
        # Energy consumption (top left) - larger
        self.ax_energy = self.fig.add_subplot(gs[0, 0])
        self.setup_axis(self.ax_energy, 'Energy Consumption (kWh)', 'Time (hours)', 'Cumulative Energy (kWh)')
        
        # Temperature (top right) - larger
        self.ax_temp = self.fig.add_subplot(gs[0, 1])
        self.setup_axis(self.ax_temp, 'Zone Temperature (°C)', 'Time (hours)', 'Temperature (°C)')
        self.ax_temp.axhline(y=20, color='#e74c3c', linestyle='--', linewidth=2, alpha=0.7, label='Min Comfort (20°C)')
        self.ax_temp.axhline(y=26, color='#e74c3c', linestyle='--', linewidth=2, alpha=0.7, label='Max Comfort (26°C)')
        self.ax_temp.legend(loc='upper right', fontsize=9)
        
        # Energy savings percentage (middle left)
        self.ax_savings = self.fig.add_subplot(gs[1, 0])
        self.setup_axis(self.ax_savings, 'Energy Savings (%)', 'Time (hours)', 'Savings (%)')
        self.ax_savings.axhline(y=0, color='#e74c3c', linestyle='-', linewidth=2, alpha=0.5)
        
        # Power consumption (middle right)
        self.ax_power = self.fig.add_subplot(gs[1, 1])
        self.setup_axis(self.ax_power, 'Power Consumption (W)', 'Time (hours)', 'Power (W)')
        
        # Metrics summary (bottom - spans both columns, more space)
        self.ax_summary = self.fig.add_subplot(gs[2:, :])
        self.ax_summary.axis('off')
        self.summary_table = None  # Will be created programmatically
        
        # Initialize lines with better colors and styles
        self.line_baseline_energy, = self.ax_energy.plot([], [], color='#3498db', label='Baseline', 
                                                          linewidth=2.5, alpha=0.8)
        self.line_controlled_energy, = self.ax_energy.plot([], [], color='#27ae60', label='AI Controlled', 
                                                            linewidth=2.5, alpha=0.8)
        self.ax_energy.legend(loc='upper left', fontsize=10, framealpha=0.9)
        
        self.line_baseline_temp, = self.ax_temp.plot([], [], color='#3498db', label='Baseline', 
                                                      linewidth=1.5, alpha=0.6)
        self.line_controlled_temp, = self.ax_temp.plot([], [], color='#27ae60', label='AI Controlled', 
                                                        linewidth=1.5, alpha=0.6)
        
        self.line_savings, = self.ax_savings.plot([], [], color='#e67e22', linewidth=2.5, alpha=0.8)
        
        self.line_baseline_power, = self.ax_power.plot(
    [], [],
    color='#3498db',
    marker='o',
    linestyle='None',
    markersize=3,
    label='Baseline'
)

        self.line_controlled_power, = self.ax_power.plot(
            [], [],
            color='#27ae60',
            marker='o',
            linestyle='None',
            markersize=3,
            label='AI Controlled'
        )
        self.ax_power.legend(loc='upper right', fontsize=10, framealpha=0.9)
        
        self.start_time = time.time()
    
    def setup_axis(self, ax, title, xlabel, ylabel):
        """Setup axis with consistent styling."""
        ax.set_title(title, fontsize=12, fontweight='bold', color='#2c3e50', pad=10)
        ax.set_xlabel(xlabel, fontsize=10, color='#34495e')
        ax.set_ylabel(ylabel, fontsize=10, color='#34495e')
        ax.tick_params(axis='both', which='major', labelsize=9, colors='#34495e')
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.set_facecolor('#fafafa')
        
    def load_data(self):
        """Load latest data from CSV files."""
        try:
            if self.baseline_file.exists():
                self.baseline_data = pd.read_csv(self.baseline_file)
            if self.controlled_file.exists():
                self.controlled_data = pd.read_csv(self.controlled_file)
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def calculate_metrics(self):
        """Calculate current metrics."""
        if len(self.baseline_data) == 0 or len(self.controlled_data) == 0:
            return None
        
        # Calculate cumulative energy
        baseline_cumulative = (self.baseline_data['fan_power'] + 
                              self.baseline_data['chiller_power'] + 
                              self.baseline_data['pump_power']).cumsum() / 1000
        controlled_cumulative = (self.controlled_data['fan_power'] + 
                                self.controlled_data['chiller_power'] + 
                                self.controlled_data['pump_power']).cumsum() / 1000
        
        # Calculate savings percentage
        if len(baseline_cumulative) > 0 and len(controlled_cumulative) > 0:
            min_len = min(len(baseline_cumulative), len(controlled_cumulative))
            savings = ((baseline_cumulative[:min_len] - controlled_cumulative[:min_len]) / 
                      baseline_cumulative[:min_len] * 100)
        else:
            savings = []
        
        # Calculate current power
        baseline_power = (self.baseline_data['fan_power'] + 
                         self.baseline_data['chiller_power'] + 
                         self.baseline_data['pump_power'])
        controlled_power = (self.controlled_data['fan_power'] + 
                           self.controlled_data['chiller_power'] + 
                           self.controlled_data['pump_power'])
        
        return {
            'baseline_cumulative': baseline_cumulative,
            'controlled_cumulative': controlled_cumulative,
            'savings': savings,
            'baseline_power': baseline_power,
            'controlled_power': controlled_power,
            'baseline_temp': self.baseline_data['zone_temp'],
            'controlled_temp': self.controlled_data['zone_temp'],
            'baseline_timestamp': self.baseline_data['timestamp'],
            'controlled_timestamp': self.controlled_data['timestamp']
        }
    
    def update_plots(self, metrics):
        """Update all plots with new metrics."""
        if metrics is None:
            return
        
        # Update energy plot
        self.line_baseline_energy.set_data(metrics['baseline_timestamp'], metrics['baseline_cumulative'])
        self.line_controlled_energy.set_data(metrics['controlled_timestamp'], metrics['controlled_cumulative'])
        
        if len(metrics['baseline_timestamp']) > 0:
            self.ax_energy.set_xlim(0, max(metrics['baseline_timestamp'].max(), metrics['controlled_timestamp'].max()) + 1)
            self.ax_energy.set_ylim(0, max(metrics['baseline_cumulative'].max(), metrics['controlled_cumulative'].max()) * 1.1)
        
        # Update temperature plot
        self.line_baseline_temp.set_data(metrics['baseline_timestamp'], metrics['baseline_temp'])
        self.line_controlled_temp.set_data(metrics['controlled_timestamp'], metrics['controlled_temp'])
        
        if len(metrics['baseline_timestamp']) > 0:
            self.ax_temp.set_xlim(0, max(metrics['baseline_timestamp'].max(), metrics['controlled_timestamp'].max()) + 1)
            self.ax_temp.set_ylim(15, 30)
        
        # Update savings plot
        if len(metrics['savings']) > 0:
            self.line_savings.set_data(metrics['controlled_timestamp'][:len(metrics['savings'])], metrics['savings'])
            self.ax_savings.set_xlim(0, metrics['controlled_timestamp'].max() + 1)
            self.ax_savings.set_ylim(-20, 50)
        
        # Update power plot
        # Update power plot
        min_len = min(
            len(metrics['baseline_timestamp']),
            len(metrics['baseline_power'])
        )

        self.line_baseline_power.set_data(
            metrics['baseline_timestamp'][:min_len],
            metrics['baseline_power'][:min_len]
        )

        min_len = min(
            len(metrics['controlled_timestamp']),
            len(metrics['controlled_power'])
        )

        self.line_controlled_power.set_data(
            metrics['controlled_timestamp'][:min_len],
            metrics['controlled_power'][:min_len]
        )

        if min_len > 0:
            max_time = max(
                metrics['baseline_timestamp'][:min_len].max(),
                metrics['controlled_timestamp'][:min_len].max()
            )

            max_power = max(
                metrics['baseline_power'][:min_len].max(),
                metrics['controlled_power'][:min_len].max()
            )

            self.ax_power.set_xlim(0, max_time + 1)
            self.ax_power.set_ylim(0, max_power * 1.1)
        
        # Update summary table programmatically
        if len(metrics['baseline_cumulative']) > 0 and len(metrics['controlled_cumulative']) > 0:
            baseline_total = metrics['baseline_cumulative'].iloc[-1]
            controlled_total = metrics['controlled_cumulative'].iloc[-1]
            energy_savings = baseline_total - controlled_total
            savings_percent = (energy_savings / baseline_total) * 100 if baseline_total > 0 else 0
            
            baseline_avg_temp = metrics['baseline_temp'].mean()
            controlled_avg_temp = metrics['controlled_temp'].mean()
            
            # Calculate comfort compliance
            min_comfort, max_comfort = 20.0, 26.0
            baseline_violations = ((metrics['baseline_temp'] > max_comfort) | (metrics['baseline_temp'] < min_comfort)).sum()
            controlled_violations = ((metrics['controlled_temp'] > max_comfort) | (metrics['controlled_temp'] < min_comfort)).sum()
            baseline_compliance = (1 - baseline_violations / len(metrics['baseline_temp'])) * 100
            controlled_compliance = (1 - controlled_violations / len(metrics['controlled_temp'])) * 100
            
            status_color = "SAVING ENERGY" if savings_percent > 0 else "USING MORE ENERGY"
            status_emoji = "✓" if savings_percent > 0 else "✗"
            
            # Create table data programmatically
            table_data = [
                ['Metric', 'Baseline', 'AI Controlled', 'Difference'],
                ['Total Energy (kWh)', f'{baseline_total:.2f}', f'{controlled_total:.2f}', f'{energy_savings:.2f}'],
                ['Avg Temperature (°C)', f'{baseline_avg_temp:.2f}', f'{controlled_avg_temp:.2f}', f'{controlled_avg_temp - baseline_avg_temp:.2f}'],
                ['Comfort Level (%)', f'{baseline_compliance:.1f}', f'{controlled_compliance:.1f}', f'{controlled_compliance - baseline_compliance:.1f}'],
                ['Data Points', f'{len(metrics["baseline_timestamp"])}', f'{len(metrics["controlled_timestamp"])}', f'{len(metrics["controlled_timestamp"]) - len(metrics["baseline_timestamp"])}'],
                ['', '', '', ''],
                ['Energy Savings', '', '', f'{savings_percent:.2f}%'],
                ['Status', '', '', f'{status_emoji} {status_color}']
            ]
            
            # Remove old table if exists
            if self.summary_table is not None:
                self.summary_table.remove()
            
            # Create new table
            self.summary_table = self.ax_summary.table(
                cellText=table_data,
                cellLoc='center',
                loc='center',
                colWidths=[0.25, 0.25, 0.25, 0.25],
                bbox=[0.1, 0.1, 0.9, 0.9]
            )
            
            # Style the table
            self.summary_table.auto_set_font_size(False)
            self.summary_table.set_fontsize(10)
            self.summary_table.scale(1, 2)
            
            # Color the header row
            for i in range(4):
                self.summary_table[(0, i)].set_facecolor('#3498db')
                self.summary_table[(0, i)].set_text_props(weight='bold', color='white')
            
            # Color the savings row
            self.summary_table[(6, 3)].set_facecolor('#27ae60' if savings_percent > 0 else '#e74c3c')
            self.summary_table[(6, 3)].set_text_props(weight='bold', color='white')
            
            # Color the status row
            self.summary_table[(7, 3)].set_facecolor('#27ae60' if savings_percent > 0 else '#e74c3c')
            self.summary_table[(7, 3)].set_text_props(weight='bold', color='white')
    
    def update(self, frame):
        """Update function for animation."""
        self.load_data()
        metrics = self.calculate_metrics()
        self.update_plots(metrics)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        return self.line_baseline_energy, self.line_controlled_energy
    
    def run(self):
        """Run the live dashboard."""
        print("=" * 60)
        print("Live Monitoring Dashboard Started")
        print("=" * 60)
        print(f"Baseline file: {self.baseline_file}")
        print(f"Controlled file: {self.controlled_file}")
        print(f"Update interval: {self.update_interval} seconds")
        print()
        print("Monitoring simulation... Close the window to stop.")
        print()
        
        # Create animation and keep reference
        self.anim = FuncAnimation(self.fig, self.update, interval=self.update_interval*1000, cache_frame_data=False)
        
        # Show plot and keep window open
        plt.show(block=True)
        
        print("\nDashboard stopped.")


def main():
    """Main function to run live dashboard."""
    project_root = Path(__file__).parent
    
    # Default file paths
    baseline_file = project_root / "output" / "baseline" / "simulation_data" / "simulation_data.csv"
    controlled_file = project_root / "output" / "ai_controlled_basic" / "simulation_data" / "simulation_data.csv"
    
    # Check if files exist
    if not baseline_file.exists():
        print(f"[WARNING] Baseline file not found: {baseline_file}")
        print("Run 'python main.py 1' to generate baseline data first.")
        print("Dashboard will wait for file to be created...")
    
    if not controlled_file.exists():
        print(f"[WARNING] Controlled file not found: {controlled_file}")
        print("Run 'python main.py 2' to generate AI control data first.")
        print("Dashboard will wait for file to be created...")
    
    # Create and run dashboard
    dashboard = LiveDashboard(baseline_file, controlled_file, update_interval=2)
    dashboard.run()


if __name__ == "__main__":
    main()
