"""
Quick test script to verify AI controller functionality without running full simulation
"""
import asyncio
import json
from pathlib import Path
import sys

ENERGYPLUS_PATH = r"C:\EnergyPlusV26-1-0"
sys.path.insert(0, ENERGYPLUS_PATH)

from controller.ai_controller import AIController
from llm_integration import create_llm_integration

def test_llm_integration():
    """Test LLM integration directly"""
    print("=" * 60)
    print("Testing LLM Integration")
    print("=" * 60)
    
    # Load config
    config_file = Path(__file__).parent / "llm_config.json"
    with open(config_file, 'r') as f:
        llm_config = json.load(f)
    
    print(f"Config loaded: {llm_config['provider']} - {llm_config['model']}")
    
    # Test LLM directly
    llm = create_llm_integration(llm_config)
    
    test_data = {
        'zone_temp': 24.0,
        'outdoor_temp': 25.0,
        'hvac_power': 3000,
        'timestamp': 36000
    }
    
    print(f"\nTest data: {test_data}")
    print("Calling LLM...")
    
    result = asyncio.run(llm.compute_control_actions(test_data))
    
    print(f"\nLLM Response:")
    print(f"Cooling setpoint: {result.get('cooling_setpoint')}")
    print(f"Heating setpoint: {result.get('heating_setpoint')}")
    print(f"Reasoning: {result.get('reasoning')}")
    print(f"Strategy: {result.get('strategy')}")
    
    return result

def test_ai_controller():
    """Test AI Controller"""
    print("\n" + "=" * 60)
    print("Testing AI Controller")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    
    # Load config
    config_file = project_root / "llm_config.json"
    with open(config_file, 'r') as f:
        llm_config = json.load(f)
    
    # Create AI controller
    controller = AIController(project_root, use_ai=True, llm_config=llm_config)
    
    # Test with multiple scenarios
    test_scenarios = [
        {
            'name': 'Hot day - occupied',
            'data': {'zone_temp': 27.0, 'outdoor_temp': 30.0, 'hvac_power': 5000, 'timestamp': 36000}
        },
        {
            'name': 'Cold day - occupied', 
            'data': {'zone_temp': 19.0, 'outdoor_temp': 5.0, 'hvac_power': 4000, 'timestamp': 36000}
        },
        {
            'name': 'Comfortable - occupied',
            'data': {'zone_temp': 23.0, 'outdoor_temp': 22.0, 'hvac_power': 2000, 'timestamp': 36000}
        },
        {
            'name': 'Unoccupied - night',
            'data': {'zone_temp': 22.0, 'outdoor_temp': 15.0, 'hvac_power': 1000, 'timestamp': 72000}
        }
    ]
    
    results = []
    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']} ---")
        print(f"Input: {scenario['data']}")
        
        actions = controller.compute_control_actions(scenario['data'])
        
        print(f"Output:")
        print(f"  Cooling setpoint: {actions['cooling_setpoint']}")
        print(f"  Heating setpoint: {actions['heating_setpoint']}")
        print(f"  Strategy: {actions['strategy']}")
        print(f"  Reasoning: {actions['reasoning'][:100]}...")
        
        results.append({
            'scenario': scenario['name'],
            'cooling_setpoint': actions['cooling_setpoint'],
            'heating_setpoint': actions['heating_setpoint'],
            'strategy': actions['strategy']
        })
    
    return results

def main():
    """Run all tests"""
    print("\nAI Controller Functionality Test")
    print("=" * 60)
    
    try:
        # Test 1: LLM Integration
        llm_result = test_llm_integration()
        
        # Test 2: AI Controller
        controller_results = test_ai_controller()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("[OK] LLM integration working")
        print("[OK] AI controller functional")
        print(f"[OK] Tested {len(controller_results)} scenarios")
        
        print("\nAI Controller Results:")
        for result in controller_results:
            print(f"  {result['scenario']}:")
            print(f"    Cooling: {result['cooling_setpoint']}°C, Heating: {result['heating_setpoint']}°C")
            print(f"    Strategy: {result['strategy']}")
        
        print("\n[SUCCESS] AI controller is ready for EnergyPlus simulation")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
