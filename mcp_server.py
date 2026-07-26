"""
MCP Server for Eco-Loop Building Agents
This server provides tools for LLMs to interact with EnergyPlus simulations
and perform autonomous building control operations.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# MCP imports (will need to install mcp package)
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
except ImportError:
    print("MCP package not installed. Install with: pip install mcp")

# Import LLM integration
try:
    from llm_integration import LLMIntegration, create_llm_integration
except ImportError:
    print("llm_integration module not found")
    LLMIntegration = None


class BuildingMCPServer:
    """MCP Server for building energy management and control."""

    def __init__(self, project_root: Path, llm_config: Optional[Dict] = None):
        self.project_root = project_root
        self.server = Server("eco-loop-building-agents")

        # Initialize LLM integration if available
        self.llm_integration = None
        if LLMIntegration:
            try:
                self.llm_integration = create_llm_integration(llm_config)
                print("LLM integration initialized successfully")
            except Exception as e:
                print(f"LLM integration failed: {e}")

        # Register tools
        self._register_tools()

        # Current simulation state
        self.current_sensor_data: Optional[Dict] = None
        self.current_setpoints: Dict = {
            'cooling_setpoint': 24.0,
            'heating_setpoint': 20.0
        }

    def _register_tools(self):
        """Register all available tools with the MCP server."""

        @self.server.tool(
            name="get_current_sensor_data",
            description="Get current sensor readings from the building simulation including zone temperature, outdoor temperature, and energy consumption metrics."
        )
        async def get_current_sensor_data() -> List[TextContent]:
            """Retrieve current sensor data from the simulation."""
            if self.current_sensor_data is None:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": "No simulation data available. Run a simulation first."
                    }, indent=2)
                )]

            return [TextContent(
                type="text",
                text=json.dumps({
                    "status": "success",
                    "data": self.current_sensor_data,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
            )]

        @self.server.tool(
            name="analyze_building_performance",
            description="Analyze building performance metrics including energy consumption, thermal comfort, and efficiency. Returns comprehensive analysis with recommendations."
        )
        async def analyze_building_performance(
            comfort_min_temp: float = 20.0,
            comfort_max_temp: float = 26.0
        ) -> List[TextContent]:
            """Analyze current building performance."""
            if self.current_sensor_data is None:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": "No simulation data available."
                    }, indent=2)
                )]

            zone_temp = self.current_sensor_data.get('zone_temp', 0)
            outdoor_temp = self.current_sensor_data.get('outdoor_temp', 0)
            hvac_power = self.current_sensor_data.get('hvac_power', 0)

            # Comfort analysis
            comfort_status = "comfortable"
            if zone_temp > comfort_max_temp:
                comfort_status = "too_hot"
            elif zone_temp < comfort_min_temp:
                comfort_status = "too_cold"

            # Energy efficiency analysis
            efficiency_rating = "good"
            if hvac_power > 5000:
                efficiency_rating = "poor"
            elif hvac_power > 3000:
                efficiency_rating = "moderate"

            analysis = {
                "status": "success",
                "analysis": {
                    "thermal_comfort": {
                        "zone_temperature": zone_temp,
                        "outdoor_temperature": outdoor_temp,
                        "comfort_status": comfort_status,
                        "comfort_range": f"{comfort_min_temp}-{comfort_max_temp}°C",
                        "deviation_from_comfort": max(
                            0, max(zone_temp - comfort_max_temp, comfort_min_temp - zone_temp)
                        )
                    },
                    "energy_consumption": {
                        "hvac_power_w": hvac_power,
                        "efficiency_rating": efficiency_rating,
                        "fan_power_w": self.current_sensor_data.get('fan_power', 0),
                        "chiller_power_w": self.current_sensor_data.get('chiller_power', 0),
                        "pump_power_w": self.current_sensor_data.get('pump_power', 0)
                    },
                    "current_setpoints": self.current_setpoints,
                    "recommendations": self._generate_recommendations(
                        comfort_status, efficiency_rating, zone_temp, outdoor_temp
                    )
                },
                "timestamp": datetime.now().isoformat()
            }

            return [TextContent(
                type="text",
                text=json.dumps(analysis, indent=2)
            )]

        @self.server.tool(
            name="compute_optimal_setpoints",
            description="Compute optimal cooling and heating setpoints based on current conditions, occupancy, and energy optimization goals. Uses LLM integration if available, otherwise falls back to rule-based reasoning."
        )
        async def compute_optimal_setpoints(
            occupied: bool = True,
            energy_priority: str = "balanced",
            outdoor_temp: Optional[float] = None,
            use_llm: bool = True
        ) -> List[TextContent]:
            """Compute optimal setpoints using AI reasoning."""
            if self.current_sensor_data is None:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": "No simulation data available."
                    }, indent=2)
                )]

            zone_temp = self.current_sensor_data.get('zone_temp', 24.0)
            if outdoor_temp is None:
                outdoor_temp = self.current_sensor_data.get('outdoor_temp', 20.0)

            # Try LLM integration first if available and requested
            if use_llm and self.llm_integration:
                try:
                    llm_actions = await self.llm_integration.compute_control_actions(self.current_sensor_data)
                    recommendations = {
                        "status": "success",
                        "method": "llm",
                        "recommendations": {
                            "cooling_setpoint": llm_actions.get('cooling_setpoint', 24.0),
                            "heating_setpoint": llm_actions.get('heating_setpoint', 20.0),
                            "reasoning": llm_actions.get('reasoning', 'LLM-based optimization'),
                            "strategy": llm_actions.get('strategy', 'balanced'),
                            "llm_provider": llm_actions.get('llm_provider', 'unknown')
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    return [TextContent(
                        type="text",
                        text=json.dumps(recommendations, indent=2)
                    )]
                except Exception as e:
                    print(f"LLM computation failed, falling back to rule-based: {e}")

            # Fallback to rule-based reasoning
            if occupied:
                if energy_priority == "energy_saving":
                    # More aggressive energy saving during occupied hours
                    cooling_setpoint = min(26.0, max(22.0, zone_temp + 0.5))
                    heating_setpoint = max(18.0, min(21.0, zone_temp - 0.5))
                elif energy_priority == "comfort":
                    # Prioritize comfort
                    cooling_setpoint = 23.0
                    heating_setpoint = 21.0
                else:  # balanced
                    cooling_setpoint = 24.0
                    heating_setpoint = 20.0
            else:
                # Unoccupied - wider comfort band
                cooling_setpoint = 27.0
                heating_setpoint = 17.0

            # Adjust based on outdoor conditions
            if outdoor_temp > 28:  # Very hot outside
                cooling_setpoint = min(26.0, cooling_setpoint + 0.5)
            elif outdoor_temp < 15:  # Cold outside
                heating_setpoint = max(18.0, heating_setpoint - 0.5)

            recommendations = {
                "status": "success",
                "method": "rule_based",
                "recommendations": {
                    "cooling_setpoint": round(cooling_setpoint, 1),
                    "heating_setpoint": round(heating_setpoint, 1),
                    "reasoning": {
                        "occupied": occupied,
                        "energy_priority": energy_priority,
                        "outdoor_conditions": outdoor_temp,
                        "current_zone_temp": zone_temp,
                        "strategy": self._explain_strategy(occupied, energy_priority, outdoor_temp)
                    }
                },
                "timestamp": datetime.now().isoformat()
            }

            return [TextContent(
                type="text",
                text=json.dumps(recommendations, indent=2)
            )]

        @self.server.tool(
            name="apply_control_actions",
            description="Apply computed control actions by setting new cooling and heating setpoints in the building simulation."
        )
        async def apply_control_actions(
            cooling_setpoint: float,
            heating_setpoint: float
        ) -> List[TextContent]:
            """Apply control actions to the simulation."""
            # Validate setpoints
            if not (18.0 <= cooling_setpoint <= 30.0):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": f"Invalid cooling setpoint: {cooling_setpoint}. Must be between 18-30°C."
                    }, indent=2)
                )]

            if not (15.0 <= heating_setpoint <= 25.0):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": f"Invalid heating setpoint: {heating_setpoint}. Must be between 15-25°C."
                    }, indent=2)
                )]

            # Apply setpoints
            self.current_setpoints['cooling_setpoint'] = cooling_setpoint
            self.current_setpoints['heating_setpoint'] = heating_setpoint

            result = {
                "status": "success",
                "actions_applied": {
                    "cooling_setpoint": cooling_setpoint,
                    "heating_setpoint": heating_setpoint
                },
                "previous_setpoints": {
                    "cooling_setpoint": self.current_setpoints.get('cooling_setpoint', 24.0),
                    "heating_setpoint": self.current_setpoints.get('heating_setpoint', 20.0)
                },
                "timestamp": datetime.now().isoformat()
            }

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]

        @self.server.tool(
            name="get_simulation_status",
            description="Get the current status of the building simulation including runtime information, data availability, and system health."
        )
        async def get_simulation_status() -> List[TextContent]:
            """Get simulation status."""
            status = {
                "status": "success",
                "simulation_status": {
                    "data_available": self.current_sensor_data is not None,
                    "current_setpoints": self.current_setpoints,
                    "project_root": str(self.project_root),
                    "server_time": datetime.now().isoformat()
                }
            }

            if self.current_sensor_data:
                status["simulation_status"]["last_data_timestamp"] = self.current_sensor_data.get('timestamp', 0)
                status["simulation_status"]["current_zone_temp"] = self.current_sensor_data.get('zone_temp', 0)

            return [TextContent(
                type="text",
                text=json.dumps(status, indent=2)
            )]

        @self.server.tool(
            name="load_historical_data",
            description="Load historical simulation data from CSV files for trend analysis and pattern recognition."
        )
        async def load_historical_data(
            data_file: str = "simulation_data.csv"
        ) -> List[TextContent]:
            """Load historical simulation data."""
            import pandas as pd

            data_path = self.project_root / "output" / "simulation_data" / data_file

            if not data_path.exists():
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": f"Data file not found: {data_path}"
                    }, indent=2)
                )]

            try:
                df = pd.read_csv(data_path)
                summary = {
                    "status": "success",
                    "data_summary": {
                        "rows": len(df),
                        "columns": list(df.columns),
                        "time_range": {
                            "start": df['timestamp'].min() if 'timestamp' in df.columns else None,
                            "end": df['timestamp'].max() if 'timestamp' in df.columns else None
                        },
                        "statistics": {
                            "avg_zone_temp": df['zone_temp'].mean() if 'zone_temp' in df.columns else None,
                            "avg_hvac_power": df['hvac_power'].mean() if 'hvac_power' in df.columns else None,
                            "total_energy_kwh": df['hvac_power'].sum() / 1000 if 'hvac_power' in df.columns else None
                        }
                    }
                }

                return [TextContent(
                    type="text",
                    text=json.dumps(summary, indent=2)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "error",
                        "message": f"Error loading data: {str(e)}"
                    }, indent=2)
                )]

    def _generate_recommendations(
        self, comfort_status: str, efficiency_rating: str,
        zone_temp: float, outdoor_temp: float
    ) -> List[str]:
        """Generate recommendations based on current conditions."""
        recommendations = []

        if comfort_status == "too_hot":
            recommendations.append("Zone temperature is above comfort range. Consider lowering cooling setpoint.")
        elif comfort_status == "too_cold":
            recommendations.append("Zone temperature is below comfort range. Consider raising heating setpoint.")

        if efficiency_rating == "poor":
            recommendations.append("High energy consumption detected. Consider relaxing setpoints during unoccupied hours.")

        if outdoor_temp > 25 and zone_temp < 24:
            recommendations.append("Outdoor temperature is high but zone is cool. Opportunity to raise cooling setpoint for energy savings.")

        if outdoor_temp < 15 and zone_temp > 22:
            recommendations.append("Outdoor temperature is low but zone is warm. Opportunity to lower heating setpoint for energy savings.")

        if not recommendations:
            recommendations.append("Current conditions are optimal. Continue monitoring.")

        return recommendations

    def _explain_strategy(self, occupied: bool, energy_priority: str, outdoor_temp: float) -> str:
        """Explain the control strategy used."""
        if not occupied:
            return "Unoccupied mode: Using wide comfort band (17-27°C) for maximum energy savings"

        if energy_priority == "energy_saving":
            return f"Energy saving mode: Aggressively optimizing setpoints, outdoor temp is {outdoor_temp}°C"
        elif energy_priority == "comfort":
            return "Comfort priority mode: Maintaining tight comfort band (21-23°C)"
        else:
            return f"Balanced mode: Standard setpoints with outdoor temp consideration ({outdoor_temp}°C)"

    def update_sensor_data(self, sensor_data: Dict):
        """Update current sensor data (called by simulation callback)."""
        self.current_sensor_data = sensor_data

    def get_current_setpoints(self) -> Dict:
        """Get current setpoints for application in simulation."""
        return self.current_setpoints


async def main():
    """Main entry point for the MCP server."""
    import sys

    project_root = Path(__file__).parent
    server = BuildingMCPServer(project_root)

    # Run the server using stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            server.server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
