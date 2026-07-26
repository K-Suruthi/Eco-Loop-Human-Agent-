"""
LLM Integration Module for Eco-Loop Building Agents
Supports local open-source LLMs via Ollama (Llama 3, Mistral, Qwen, etc.)
"""

import json
import asyncio
from typing import Dict, Optional
from pathlib import Path
import sys


class OllamaClient:
    """Client for local Ollama LLM (open-source models only)."""

    def __init__(self, model_name: str = "llama3", host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host
        self.base_url = f"{host}/api"

    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate response using Ollama API."""
        try:
            import aiohttp
        except ImportError:
            print("aiohttp not installed. Install with: pip install aiohttp")
            raise RuntimeError("aiohttp is required for Ollama integration")

        url = f"{self.base_url}/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        error_text = await response.text()
                        raise RuntimeError(f"Ollama error {response.status}: {error_text}")
        except Exception as e:
            raise RuntimeError(f"Ollama connection error: {e}")


class LLMIntegration:
    """Main LLM integration manager for open-source models via Ollama."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.client = self._create_client()
        self.system_prompt = self._build_system_prompt()

    def _default_config(self) -> Dict:
        """Default configuration for Ollama."""
        return {
            "provider": "ollama",
            "model": "llama3",
            "ollama_host": "http://localhost:11434"
        }

    def _create_client(self) -> OllamaClient:
        """Create Ollama client."""
        return OllamaClient(
            model_name=self.config.get("model", "llama3"),
            host=self.config.get("ollama_host", "http://localhost:11434")
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt for building control."""
        return """You are an expert building energy optimization AI. Your task is to control HVAC setpoints to minimize energy consumption while maintaining thermal comfort.

COMFORT CONSTRAINTS:
- Occupied hours (8 AM - 6 PM): Maintain zone temperature between 20-26°C
- Unoccupied hours: Allow wider range 17-28°C for energy savings

CONTROL OBJECTIVES:
1. Minimize HVAC energy consumption
2. Maintain thermal comfort during occupied hours
3. Adapt to outdoor weather conditions
4. Avoid rapid setpoint oscillations

RESPONSE FORMAT:
Always respond with valid JSON in this format:
{
    "cooling_setpoint": <float between 18-30>,
    "heating_setpoint": <float between 15-25>,
    "reasoning": "<brief explanation of decision>",
    "strategy": "<comfort_priority|energy_saving|balanced>"
}

Consider current conditions, outdoor temperature, occupancy, and energy consumption when making decisions."""

    async def compute_control_actions(self, sensor_data: Dict) -> Dict:
        """Compute control actions using LLM."""
        prompt = self._build_control_prompt(sensor_data)

        response = await self.client.generate_response(prompt, self.system_prompt)

        # Parse JSON response
        try:
            actions = json.loads(response)

            # Validate and sanitize
            actions = self._validate_actions(actions)

            return {
                **actions,
                "control_strategy": "llm",
                "llm_provider": self.config.get("provider"),
                "llm_model": self.config.get("model")
            }
        except json.JSONDecodeError as e:
            # Try to extract JSON from response if it's embedded in text
            try:
                # Look for JSON-like content in the response
                import re
                json_match = re.search(r'\{[^{}]*\}', response)
                if json_match:
                    actions = json.loads(json_match.group())
                    actions = self._validate_actions(actions)
                    return {
                        **actions,
                        "control_strategy": "llm",
                        "llm_provider": self.config.get("provider"),
                        "llm_model": self.config.get("model")
                    }
            except:
                pass

            raise RuntimeError(f"Failed to parse LLM response: {response}")

    def _build_control_prompt(self, sensor_data: Dict) -> str:
        """Build control prompt from sensor data."""
        zone_temp = sensor_data.get('zone_temp', 24.0)
        outdoor_temp = sensor_data.get('outdoor_temp', 20.0)
        hvac_power = sensor_data.get('hvac_power', 0)
        timestamp = sensor_data.get('timestamp', 0)

        # Determine occupancy
        hour = int((timestamp % 86400) / 3600)
        occupied = 8 <= hour <= 18

        prompt = f"""CURRENT BUILDING CONDITIONS:

Zone Temperature: {zone_temp:.2f}°C
Outdoor Temperature: {outdoor_temp:.2f}°C
HVAC Power Consumption: {hvac_power:.2f} W
Current Time: {hour}:00 (Hour of day)
Occupancy: {'Occupied' if occupied else 'Unoccupied'}

TASK:
Compute optimal cooling and heating setpoints for the next time step.

Consider:
- Current zone temperature vs comfort range
- Outdoor temperature trends
- Energy consumption level
- Occupancy status

Provide your response as JSON with cooling_setpoint, heating_setpoint, reasoning, and strategy."""

        return prompt

    def _validate_actions(self, actions: Dict) -> Dict:
        """Validate and sanitize control actions."""
        cooling_setpoint = actions.get('cooling_setpoint')
        heating_setpoint = actions.get('heating_setpoint')

        # Handle None values
        if cooling_setpoint is None:
            cooling_setpoint = 24.0
        if heating_setpoint is None:
            heating_setpoint = 20.0

        # Convert to float if needed
        try:
            cooling_setpoint = float(cooling_setpoint)
            heating_setpoint = float(heating_setpoint)
        except (TypeError, ValueError):
            cooling_setpoint = 24.0
            heating_setpoint = 20.0

        # Clamp to safe ranges
        cooling_setpoint = max(18.0, min(30.0, cooling_setpoint))
        heating_setpoint = max(15.0, min(25.0, heating_setpoint))

        # Ensure heating < cooling
        if heating_setpoint >= cooling_setpoint:
            heating_setpoint = cooling_setpoint - 2.0

        return {
            'cooling_setpoint': round(cooling_setpoint, 1),
            'heating_setpoint': round(heating_setpoint, 1),
            'reasoning': actions.get('reasoning', 'LLM-based optimization'),
            'strategy': actions.get('strategy', 'balanced')
        }

    def update_config(self, new_config: Dict):
        """Update configuration."""
        self.config.update(new_config)
        self.client = self._create_client()


def create_llm_integration(config: Optional[Dict] = None) -> LLMIntegration:
    """Factory function to create LLM integration."""
    return LLMIntegration(config)


# Test function
async def test_llm_integration():
    """Test LLM integration."""
    config = {
        "provider": "ollama",
        "model": "llama3"
    }

    llm = create_llm_integration(config)

    test_sensor_data = {
        'zone_temp': 25.5,
        'outdoor_temp': 28.0,
        'hvac_power': 3500,
        'timestamp': 36000  # 10 AM
    }

    actions = await llm.compute_control_actions(test_sensor_data)
    print("Control Actions:", json.dumps(actions, indent=2))


if __name__ == "__main__":
    asyncio.run(test_llm_integration())
