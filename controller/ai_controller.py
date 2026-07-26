"""
AI Controller for Eco-Loop Building Agents
Integrates with LLM integration module for real AI-driven building control using open-source models.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Optional
import sys

ENERGYPLUS_PATH = r"C:\EnergyPlusV26-1-0"
sys.path.insert(0, ENERGYPLUS_PATH)

# Import LLM integration
try:
    from llm_integration import LLMIntegration, create_llm_integration
    LLM_AVAILABLE = True
except ImportError:
    print("llm_integration module not found")
    LLM_AVAILABLE = False


class AIController:
    """
    AI-driven controller that uses open-source LLM for building control decisions.
    Requires LLM to be available - no fallback to rule-based control.
    """

    def __init__(self, project_root: Path, use_ai: bool = True, llm_config: Optional[Dict] = None):
        self.project_root = project_root
        self.use_ai = use_ai and LLM_AVAILABLE

        # Initialize LLM integration (required)
        if not self.use_ai:
            raise RuntimeError("AI controller requires LLM integration. Please run: python setup_llm.py")

        try:
            self.llm_integration = create_llm_integration(llm_config)
            print("LLM integration initialized successfully")
        except Exception as e:
            raise RuntimeError(f"LLM integration failed: {e}. Please ensure Ollama is installed and configured.")

        # Current setpoints
        self.current_cooling_setpoint = 24.0
        self.current_heating_setpoint = 20.0

        # Control history
        self.control_history = []

        # Async event loop for LLM calls
        self.loop = None

    def compute_control_actions(self, sensor_data: Dict) -> Dict:
        """
        Compute control actions using LLM only.
        This is the main decision-making function called during simulation.
        """
        if not self.llm_integration:
            raise RuntimeError("LLM integration not available")

        try:
            # AI-based control (run async in sync context)
            ai_actions = self._compute_ai_actions_sync(sensor_data)
            if ai_actions:
                self._log_control_decision(sensor_data, ai_actions, "llm")
                return ai_actions
        except Exception as e:
            raise RuntimeError(f"AI control failed: {e}")

        raise RuntimeError("Failed to compute AI control actions")

    def _compute_ai_actions_sync(self, sensor_data: Dict) -> Optional[Dict]:
        """Compute AI actions synchronously by running async in event loop."""
        try:
            # Create new event loop if needed
            if self.loop is None or self.loop.is_closed():
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)

            # Run the async function
            ai_actions = self.loop.run_until_complete(
                self.llm_integration.compute_control_actions(sensor_data)
            )

            # Smooth setpoint changes
            cooling_setpoint = self._smooth_setpoint(
                self.current_cooling_setpoint,
                ai_actions.get('cooling_setpoint', 24.0),
                max_change=1.0
            )
            heating_setpoint = self._smooth_setpoint(
                self.current_heating_setpoint,
                ai_actions.get('heating_setpoint', 20.0),
                max_change=1.0
            )

            # Update current setpoints
            self.current_cooling_setpoint = cooling_setpoint
            self.current_heating_setpoint = heating_setpoint

            return {
                'cooling_setpoint': cooling_setpoint,
                'heating_setpoint': heating_setpoint,
                'reasoning': ai_actions.get('reasoning', 'LLM-based optimization'),
                'strategy': ai_actions.get('strategy', 'balanced'),
                'control_strategy': 'llm'
            }
        except Exception as e:
            print(f"Async AI computation error: {e}")
            return None

    def _smooth_setpoint(self, current: float, target: float, max_change: float) -> float:
        """Smooth setpoint changes to avoid rapid oscillations."""
        change = target - current
        if abs(change) > max_change:
            return current + (max_change if change > 0 else -max_change)
        return target

    def _log_control_decision(self, sensor_data: Dict, actions: Dict, strategy: str):
        """Log control decisions for analysis."""
        log_entry = {
            'timestamp': sensor_data['timestamp'],
            'zone_temp': sensor_data['zone_temp'],
            'outdoor_temp': sensor_data['outdoor_temp'],
            'hvac_power': sensor_data['hvac_power'],
            'cooling_setpoint': actions['cooling_setpoint'],
            'heating_setpoint': actions['heating_setpoint'],
            'control_strategy': strategy
        }
        self.control_history.append(log_entry)

    def get_control_history(self) -> list:
        """Get history of control decisions."""
        return self.control_history

    def export_control_history(self, output_file: Path):
        """Export control history to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(self.control_history, f, indent=2)

    def reset(self):
        """Reset controller state."""
        self.current_cooling_setpoint = 24.0
        self.current_heating_setpoint = 20.0
        self.control_history = []


class EnhancedAIController(AIController):
    """
    Enhanced AI controller with more sophisticated reasoning capabilities.
    Uses LLM integration for complex reasoning with predictive capabilities.
    """

    def __init__(self, project_root: Path, use_ai: bool = True, llm_config: Optional[Dict] = None):
        super().__init__(project_root, use_ai, llm_config)
        self.prediction_window = 10  # Look ahead 10 time steps
        self.learning_rate = 0.1

    def _compute_ai_actions_sync(self, sensor_data: Dict) -> Optional[Dict]:
        """Enhanced AI control with predictive capabilities using LLM."""
        try:
            # Create new event loop if needed
            if self.loop is None or self.loop.is_closed():
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)

            # Add predictive context to sensor data
            enhanced_sensor_data = self._add_predictive_context(sensor_data)

            # Run the async function with enhanced context
            ai_actions = self.loop.run_until_complete(
                self.llm_integration.compute_control_actions(enhanced_sensor_data)
            )

            # Smooth setpoint changes
            cooling_setpoint = self._smooth_setpoint(
                self.current_cooling_setpoint,
                ai_actions.get('cooling_setpoint', 24.0),
                max_change=0.8  # Smoother transitions for enhanced mode
            )
            heating_setpoint = self._smooth_setpoint(
                self.current_heating_setpoint,
                ai_actions.get('heating_setpoint', 20.0),
                max_change=0.8
            )

            # Update current setpoints
            self.current_cooling_setpoint = cooling_setpoint
            self.current_heating_setpoint = heating_setpoint

            # Calculate scores
            comfort_score = self._calculate_comfort_score(sensor_data['zone_temp'])
            energy_score = self._calculate_energy_score(sensor_data['hvac_power'])

            return {
                'cooling_setpoint': cooling_setpoint,
                'heating_setpoint': heating_setpoint,
                'reasoning': ai_actions.get('reasoning', 'Enhanced LLM-based optimization'),
                'strategy': ai_actions.get('strategy', 'balanced'),
                'comfort_score': comfort_score,
                'energy_score': energy_score,
                'control_strategy': 'enhanced_llm'
            }
        except Exception as e:
            print(f"Enhanced AI computation error: {e}")
            return None

    def _add_predictive_context(self, sensor_data: Dict) -> Dict:
        """Add predictive context to sensor data for enhanced LLM reasoning."""
        enhanced_data = sensor_data.copy()

        # Analyze recent trends
        temp_trend = self._analyze_temperature_trend()
        energy_trend = self._analyze_energy_trend()

        # Add trend information
        enhanced_data['temperature_trend'] = temp_trend
        enhanced_data['energy_trend'] = energy_trend

        # Add predictive scores
        enhanced_data['comfort_score'] = self._calculate_comfort_score(sensor_data['zone_temp'])
        enhanced_data['energy_score'] = self._calculate_energy_score(sensor_data['hvac_power'])

        return enhanced_data

    def _analyze_temperature_trend(self) -> str:
        """Analyze temperature trend from recent data."""
        if len(self.control_history) < 5:
            return "stable"

        recent_temps = [entry['zone_temp'] for entry in self.control_history[-5:]]
        if recent_temps[-1] > recent_temps[0] + 0.5:
            return "rising"
        elif recent_temps[-1] < recent_temps[0] - 0.5:
            return "falling"
        return "stable"

    def _analyze_energy_trend(self) -> str:
        """Analyze energy consumption trend."""
        if len(self.control_history) < 5:
            return "stable"

        recent_power = [entry['hvac_power'] for entry in self.control_history[-5:]]
        if recent_power[-1] > recent_power[0] + 500:
            return "increasing"
        elif recent_power[-1] < recent_power[0] - 500:
            return "decreasing"
        return "stable"

    def _calculate_comfort_score(self, zone_temp: float) -> float:
        """Calculate comfort score (0-1 scale)."""
        min_comfort, max_comfort = 20.0, 26.0
        if min_comfort <= zone_temp <= max_comfort:
            return 1.0
        elif zone_temp > max_comfort:
            return max(0, 1 - (zone_temp - max_comfort) / 5)
        else:
            return max(0, 1 - (min_comfort - zone_temp) / 5)

    def _calculate_energy_score(self, hvac_power: float) -> float:
        """Calculate energy efficiency score (0-1 scale)."""
        # Normalize power consumption (lower is better)
        max_power = 10000  # W
        return max(0, 1 - hvac_power / max_power)

    def _optimize_cooling_setpoint(
        self, zone_temp: float, outdoor_temp: float,
        weight_comfort: float, weight_energy: float
    ) -> float:
        """Optimize cooling setpoint using weighted objectives."""
        # Comfort-driven setpoint
        comfort_setpoint = max(22.0, min(26.0, zone_temp - 0.5))

        # Energy-driven setpoint
        if outdoor_temp > 25:
            energy_setpoint = 26.0
        else:
            energy_setpoint = 24.0

        # Weighted combination
        optimal = weight_comfort * comfort_setpoint + weight_energy * energy_setpoint

        return self._smooth_setpoint(self.current_cooling_setpoint, optimal, max_change=0.8)

    def _optimize_heating_setpoint(
        self, zone_temp: float, outdoor_temp: float,
        weight_comfort: float, weight_energy: float
    ) -> float:
        """Optimize heating setpoint using weighted objectives."""
        # Comfort-driven setpoint
        comfort_setpoint = min(21.0, max(18.0, zone_temp + 0.5))

        # Energy-driven setpoint
        if outdoor_temp < 15:
            energy_setpoint = 18.0
        else:
            energy_setpoint = 20.0

        # Weighted combination
        optimal = weight_comfort * comfort_setpoint + weight_energy * energy_setpoint

        return self._smooth_setpoint(self.current_heating_setpoint, optimal, max_change=0.8)
