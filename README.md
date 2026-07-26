# Eco-Loop Building Agents

AI-powered building energy optimization system combining EnergyPlus simulation with intelligent control strategies.

## Overview

This system implements a closed-loop control pipeline for building energy optimization:
- **Simulation Engine:** EnergyPlus V26.1.0 for high-fidelity building simulation
- **Control Layer:** AI-driven controller for intelligent setpoint optimization
- **Data Management:** Real-time data logging and analysis
- **Visualization:** Matplotlib-based plotting for performance analysis
- **AI Integration:** Open-source LLM integration via Ollama (Llama 3, Mistral, Qwen, etc.)

## Project Structure

```
honeywell/
├── controller/              # Core control logic
│   ├── callbacks.py         # EnergyPlus API callbacks
│   ├── energyplus_runner.py # Simulation orchestration
│   ├── data_manager.py      # Data collection and storage
│   └── ai_controller.py     # AI-driven control
├── idf/                     # Building models
│   └── 5ZoneAirCooled.idf
├── weather/                 # Weather data
│   └── USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw
├── output/                  # Simulation results
├── main.py                  # Main entry point
├── analyzer.py              # Data analysis module
├── plot_results.py          # Results visualization script
├── llm_integration.py       # LLM integration module
├── setup_llm.py             # LLM setup script
├── requirements.txt         # Python dependencies
└── ARCHITECTURE.md          # System architecture documentation
```

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Verify EnergyPlus installation:**
```bash
python pyenergy.py
```

3. **Set up AI integration (required for AI control):**
```bash
python setup_llm.py
```

The setup script will guide you through:
- Installing LLM dependencies (aiohttp)
- Installing and configuring Ollama (local open-source LLM)
- Downloading LLM models (Llama 3, Mistral, Qwen, Phi3)
- Testing the connection

## Usage

### Running Simulations

**Interactive mode:**
```bash
python main.py
```

This will prompt you to select a simulation mode:
1. Baseline simulation (no control)
2. AI control (basic)
3. AI control (enhanced)
4. Run all and compare

**Direct execution:**
```python
from controller.energyplus_runner import EnergyPlusRunner
from controller.ai_controller import AIController

runner = EnergyPlusRunner(Path("path/to/project"))
controller = AIController(Path("path/to/project"), use_ai=True, llm_config=config)
data = runner.run_controlled(controller, "output_dir")
```

### Viewing Results

**Generate plots:**
```bash
python plot_results.py
```

This generates separate plots for:
- Temperature comparison (baseline vs AI)
- Energy component analysis (fan, chiller, pump)
- Comfort analysis (compliance, distribution, violations)
- Overall summary (energy savings, key metrics)

Plots are saved to `output/plots/` directory as PNG files.

### Data Analysis

**Run analysis script:**
```python
from analyzer import EnergyAnalyzer
from pathlib import Path

analyzer = EnergyAnalyzer(Path("output"))
results = analyzer.run_full_analysis(
    Path("output/baseline/simulation_data/simulation_data.csv"),
    Path("output/controlled/simulation_data/simulation_data.csv")
)
```

## Control Strategies

### AI Controller (Basic)
- Real open-source LLM integration for setpoint decisions
- Occupancy-aware control (8 AM - 6 PM occupied hours)
- Energy optimization based on consumption patterns
- Comfort constraints (20-26°C)
- Smooth setpoint transitions
- Requires LLM setup (no fallback)

### AI Controller (Enhanced)
- Real open-source LLM integration with predictive context
- Trend analysis (temperature, energy consumption)
- Multi-objective optimization (comfort vs. energy)
- Comfort and energy scoring
- Advanced setpoint optimization with smoother transitions
- Requires LLM setup (no fallback)

## AI Integration

The system uses open-source LLMs via Ollama for building control:

**Supported Open-Source Models:**
- **Llama 3** (Recommended, 4GB)
- **Mistral** (4GB)
- **Qwen** (4GB)
- **Phi3** (2GB)

**Setup AI Integration:**
```bash
# Run the setup script
python setup_llm.py
```

The setup script will:
- Install required dependencies (aiohttp)
- Guide you through Ollama installation
- Download LLM models
- Test the connection
- Create configuration file

**Manual Configuration:**
If you prefer manual setup, create `llm_config.json`:
```json
{
  "provider": "ollama",
  "model": "llama3",
  "ollama_host": "http://localhost:11434"
}
```

## Key Features

### Real-Time Control
- Callback-based integration with EnergyPlus
- Dynamic setpoint modification via actuators
- Sub-hourly control updates

### Data Management
- CSV logging of all sensor data
- JSON export of summary statistics
- Baseline vs. controlled comparison
- Thermal comfort analysis (ASHRAE Standard 55)

### Performance Metrics
- Energy consumption (kWh)
- Thermal comfort compliance (%)
- Component-wise breakdown (fan, chiller, pump)
- Peak demand analysis

### Visualization
- Matplotlib-based plotting for performance analysis
- Temperature comparison plots
- Energy component analysis (fan, chiller, pump)
- Comfort compliance and distribution analysis
- Overall summary with energy savings metrics

## Architecture

See `ARCHITECTURE.md` for detailed system architecture including:
- Component descriptions
- Data flow diagrams
- Tool calling architecture
- Performance optimization strategies
- Error handling and resilience

## Deliverables Status

✅ **Fully Functional Source Code** - Complete Python codebase
✅ **Building Models** - 5ZoneAirCooled.idf included
✅ **Quantitative Savings Dashboard** - Matplotlib-based plotting with visualizations
✅ **System Architecture Document** - Comprehensive ARCHITECTURE.md
✅ **AI Integration** - Complete open-source LLM integration via Ollama
⏳ **Demonstration Video** - To be recorded after testing

## Troubleshooting

**EnergyPlus API not loading:**
- Verify `ENERGYPLUS_PATH` is correct in all files
- Ensure EnergyPlus V26.1.0 is installed

**Simulation crashes:**
- Check IDF file validity
- Verify weather file path
- Review EnergyPlus error logs in output directory

**Plots not generating:**
- Ensure simulations have completed
- Check CSV files exist in output directories
- Verify matplotlib is installed: `pip install matplotlib`

## Performance Tips

- For faster development, reduce simulation period in IDF file
- Use AI controller (basic) for initial testing
- Monitor memory usage for long simulations

## Citation

If you use this system in your research, please cite:
```
Eco-Loop Building Agents: AI-Powered Building Energy Optimization
Honeywell Campus Hackathon 2026
```

## License

This project is part of the Honeywell Campus Hackathon 2026 submission.
