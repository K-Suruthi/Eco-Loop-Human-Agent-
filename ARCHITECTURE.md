# Eco-Loop Building Agents - System Architecture

## Overview

Eco-Loop Building Agents is a closed-loop building energy optimization system that combines physics-based simulation (EnergyPlus) with AI-driven control (via open-source LLMs through Ollama) to create autonomous, self-correcting building management systems. This system demonstrates real-time sensor data ingestion, LLM-based decision making, and continuous control action injection to achieve quantifiable energy savings while maintaining thermal comfort.

## System Components

### 1. Simulation Engine (EnergyPlus)

**Technology:** EnergyPlus V26.1.0 with Python API (pyenergyplus)

**Purpose:** High-fidelity building energy simulation providing real-time sensor data and accepting control actions.

**Key Features:**
- Real-time sensor data streaming (zone temperatures, energy consumption, HVAC metrics)
- Dynamic setpoint modification via actuators
- Callback-based integration for closed-loop control
- Support for various building configurations (.idf files)

**Implementation:**
- `controller/callbacks.py` - Manages EnergyPlus API callbacks
- `controller/energyplus_runner.py` - Orchestrates simulation execution
- Uses `callback_after_predictor_after_hvac_managers` for real-time control

### 2. Data Management Layer

**Technology:** Python with CSV/JSON storage, Pandas for analysis

**Purpose:** Collect, store, and analyze simulation data for performance evaluation.

**Key Features:**
- Real-time data logging during simulation
- Summary statistics calculation
- Baseline vs. controlled comparison
- Thermal comfort analysis (ASHRAE Standard 55)
- Energy consumption metrics

**Implementation:**
- `controller/data_manager.py` - Data collection and storage
- `analyzer.py` - Statistical analysis and comparison
- CSV format for time-series data
- JSON format for summary statistics

### 3. Control Layer

**Technology:** Python with rule-based and AI controllers

**Purpose:** Compute optimal setpoints based on sensor data and control objectives.

**Components:**

#### 3.1 Rule-Based Controller
- Occupancy-based scheduling (8 AM - 6 PM)
- Comfort constraint enforcement (20-26°C)
- Energy-saving setpoint relaxation during unoccupied hours
- Outdoor condition adaptation
- Deadband implementation to prevent constant cycling

#### 3.2 AI Controller (Open-Source LLM)
- **LLM Integration:** Uses Ollama with Llama 3 model for decision making
- **Direct LLM Calls:** No MCP server overhead - direct async communication
- **Enhanced reasoning with predictive capabilities**
- **Multi-objective optimization (comfort vs. energy)**
- **Trend analysis (temperature, energy consumption)**
- **Smooth setpoint transitions to prevent oscillation**
- **No fallback:** Requires LLM to be available for operation

**Implementation:**
- `controller/rule_based_controller.py` - Rule-based control logic
- `controller/ai_controller.py` - AI-driven control with Ollama integration
- `llm_integration.py` - Direct Ollama client implementation

### 4. LLM Integration (Open-Source)

**Technology:** Ollama with Llama 3 model, aiohttp for async communication

**Purpose:** Provide AI-driven decision making for building control using open-source LLMs.

**Key Features:**
- **Direct API Communication:** Async HTTP calls to local Ollama instance
- **JSON Response Parsing:** Robust extraction of control actions from LLM responses
- **Error Handling:** Graceful handling of connection issues and malformed responses
- **Validation:** Setpoint validation to ensure safe operating ranges
- **No External Dependencies:** Fully local operation using open-source models

**Implementation:**
- `llm_integration.py` - Ollama client with async support
- `setup_llm.py` - Automated Ollama installation and configuration
- `llm_config.json` - Configuration for model selection and connection

**Supported Models:**
- Llama 3 (default/recommended)
- Mistral
- Qwen
- Other Ollama-compatible models

### 5. Visualization Dashboard

**Technology:** Streamlit with Plotly

**Purpose:** Real-time visualization of energy savings and comfort metrics.

**Key Features:**
- Interactive temperature comparison plots
- Energy consumption analysis
- Cumulative energy tracking
- Setpoint change visualization
- Comfort compliance analysis
- Component-wise energy breakdown

**Implementation:**
- `dashboard.py` - Streamlit dashboard
- Plotly for interactive charts
- Real-time metrics display

## Data Flow Architecture

### Closed-Loop Control Pipeline

```
┌─────────────────┐
│  EnergyPlus     │
│  Simulation     │
└────────┬────────┘
         │ Sensor Data
         ▼
┌─────────────────┐
│  Callbacks      │
│  (Real-time)    │
└────────┬────────┘
         │
         ├──────────────┐
         │              │
         ▼              ▼
┌─────────────┐  ┌─────────────┐
│ Data Logger │  │ Controller  │
└─────────────┘  └──────┬──────┘
                         │
                  Control Actions
                         │
                         ▼
                  ┌─────────────┐
                  │  Actuators  │
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ EnergyPlus  │
                  └─────────────┘
```

### AI Integration Flow

```
┌─────────────────┐
│   LLM (Ollama)  │
│   Llama 3 Model │
└────────┬────────┘
         │ Async HTTP
         ▼
┌─────────────────┐
│ LLM Integration │
│ (Direct Client) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  AI Controller  │
│  (Bridge)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Simulation     │
└─────────────────┘
```

## File Structure

```
honeywell/
├── controller/
│   ├── __init__.py
│   ├── callbacks.py           # EnergyPlus API callbacks
│   ├── energyplus_runner.py   # Simulation orchestration
│   ├── data_manager.py        # Data collection and storage
│   ├── rule_based_controller.py  # Rule-based control logic
│   └── ai_controller.py       # AI-driven control
├── idf/
│   └── 5ZoneAirCooled.idf    # Building model
├── weather/
│   └── USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw  # Weather data
├── output/
│   ├── baseline/              # Baseline simulation results
│   ├── rule_based_controlled/ # Rule-based control results
│   └── ai_controlled/         # AI control results
├── main.py                    # Entry point
├── pyenergy.py                # EnergyPlus API test
├── analyzer.py                # Data analysis module
├── dashboard.py               # Visualization dashboard
├── mcp_server.py              # MCP server for LLM integration
└── ARCHITECTURE.md            # This document
```

## Tool Calling Architecture

### LLM Integration Design Principles

1. **Direct Communication:** Async HTTP calls to local Ollama instance
2. **Stateless Design:** Each LLM call is independent with full context
3. **Clear Interfaces:** Input/output schemas are well-defined JSON
4. **Error Handling:** Graceful degradation with informative error messages
5. **Validation:** Setpoint validation to ensure safe operating ranges

### AI Control Cycle

**Typical AI Control Cycle:**

1. **Sensor Data Collection** - Retrieve current building state from EnergyPlus
2. **Context Building** - Prepare sensor data, trends, and objectives for LLM
3. **LLM Decision Making** - Send async request to Ollama with Llama 3
4. **Response Parsing** - Extract JSON control actions from LLM response
5. **Validation** - Ensure setpoints are within safe ranges
6. **Smooth Transitions** - Apply gradual setpoint changes to prevent oscillation
7. **Actuator Control** - Apply validated setpoints to EnergyPlus simulation
8. **Repeat** - Continue for next simulation time step

### Prompt Engineering Strategy

**Context Building:**
- Current sensor readings (zone temperature, outdoor temperature, HVAC power)
- Recent trends (temperature rising/falling, energy consumption patterns)
- Comfort constraints (ASHRAE Standard 55: 20-26°C)
- Energy optimization objectives
- Occupancy status and schedule
- Time of day and season context

**Prompt Structure:**
```
You are an intelligent building HVAC controller. Analyze the current building state and recommend optimal setpoints.

Current Building State:
- Zone Temperature: {zone_temp}°C
- Outdoor Temperature: {outdoor_temp}°C
- HVAC Power Consumption: {hvac_power}W
- Occupancy Status: {occupied}
- Time: {timestamp}

Control Objectives:
1. Maintain thermal comfort (20-26°C during occupied hours)
2. Minimize energy consumption
3. Prevent rapid setpoint oscillations
4. Adapt to outdoor conditions

Recent Trends:
- Temperature Trend: {temp_trend}
- Energy Trend: {energy_trend}

Provide your response as JSON with cooling_setpoint, heating_setpoint, reasoning, and strategy.
```

**Latency Management:**
- **Async Operations:** Non-blocking HTTP calls using aiohttp
- **Connection Reuse:** Persistent connections to Ollama instance
- **Timeout Handling:** 30-second timeout with fallback to previous setpoints
- **Response Caching:** Cache recent LLM responses for similar conditions
- **Batch Processing:** Process multiple time steps efficiently

## Performance Optimization

### Simulation Performance

- **Callback Frequency:** Control updates occur after HVAC managers
- **Data Logging:** Efficient CSV writing with buffered I/O
- **Memory Management:** Periodic data flushing for long simulations

### AI Integration Performance

- **Async Operations:** Non-blocking HTTP calls using aiohttp
- **Connection Pooling:** Reuse Ollama connections
- **Request Batching:** Combine multiple operations when possible
- **Latency Management:** 30-second timeouts with graceful degradation
- **Local Processing:** No external API calls for privacy and speed

### Data Analysis Performance

- **Vectorized Operations:** Use NumPy/Pandas for bulk operations
- **Incremental Analysis:** Update statistics incrementally
- **Lazy Loading:** Load data on-demand for visualization

## Error Handling and Resilience

### Simulation Errors

- **Handle Missing Variables:** Graceful degradation if sensors unavailable
- **Actuator Failures:** Log errors and continue with previous setpoints
- **Simulation Crashes:** Automatic restart with state recovery

### AI Integration Errors

- **LLM Unavailability:** System requires LLM to be available (no fallback)
- **Timeout Handling:** Default to previous setpoints on timeout
- **Invalid Responses:** JSON parsing with regex fallback for malformed outputs
- **Connection Errors:** Retry logic with exponential backoff

### Data Management Errors

- **File I/O Errors:** Retry logic with exponential backoff
- **Corrupted Data:** Validation and recovery mechanisms
- **Storage Limits:** Automatic rotation of log files

## Security Considerations

### Actuator Safety

- **Setpoint Limits:** Hard limits on all control actions
- **Rate Limiting:** Prevent rapid setpoint oscillations
- **Emergency Override:** Manual override capability

### Data Privacy

- **Local Processing:** All data processed locally
- **No External APIs:** No cloud-based data transmission
- **Secure Storage:** Encrypted storage for sensitive data

## Extension Points

### Adding New Sensors

1. Add variable handle in `callbacks.py`
2. Update data logging in `data_manager.py`
3. Add to MCP tools if needed for AI

### Adding New Control Strategies

1. Implement controller interface in `controller/`
2. Add to `energyplus_runner.py` as option
3. Update dashboard for visualization

### Adding New LLM Models

1. Update `llm_config.json` with new model name
2. Test model compatibility with Ollama
3. Adjust prompt templates if needed for specific model characteristics

## Testing Strategy

### Unit Testing

- Test individual components in isolation
- Mock EnergyPlus API for controller testing
- Validate data management operations

### Integration Testing

- Test full simulation pipeline
- Verify closed-loop control behavior
- Validate AI integration

### Performance Testing

- Measure simulation execution time
- Test with various building models
- Validate scalability

## Deployment Considerations

### System Requirements

- **Python:** 3.8+
- **EnergyPlus:** V26.1.0
- **Memory:** 4GB+ recommended
- **Storage:** 10GB+ for simulation data

### Installation

```bash
# Install dependencies
pip install pandas numpy matplotlib seaborn streamlit plotly

# For LLM integration (Ollama)
pip install aiohttp mcp

# Run setup script for Ollama
python setup_llm.py

# EnergyPlus is pre-installed in the specified directory
```

### Configuration

- Set `ENERGYPLUS_PATH` in all controller files
- Configure weather data paths
- Set output directory locations
- Adjust comfort constraints as needed

## Future Enhancements

### Short-term

1. **Real LLM Integration:** Connect to actual LLM via MCP
2. **Multi-zone Support:** Extend to multiple building zones
3. **Weather Forecasting:** Integrate weather prediction APIs
4. **Occupancy Detection:** Add real occupancy sensing

### Long-term

1. **Reinforcement Learning:** Train RL agents for control
2. **Digital Twin:** Full building digital twin integration
3. **Grid Integration:** Demand response and grid interaction
4. **Multi-building:** Portfolio-level optimization

## Conclusion

This architecture provides a robust, extensible foundation for AI-driven building energy optimization. The modular design allows for incremental enhancement and easy integration of new technologies while maintaining backward compatibility with existing rule-based systems.
