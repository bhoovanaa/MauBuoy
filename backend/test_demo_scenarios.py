# test_demo_scenarios.py
"""
Test all 4 demo scenarios through the mock orchestrator.
This verifies the entire pipeline works correctly.
"""

import json
from demo_scenarios import DEMO_SCENARIOS
from gemma_orchestrator import GEMMA_ORCHESTRATOR

def test_all_scenarios():
    """Run all demo scenarios and verify outputs"""
    
    print("=" * 80)
    print("TESTING ALL DEMO SCENARIOS")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for scenario_id, scenario in DEMO_SCENARIOS.items():
        print(f"\n{'='*80}")
        print(f"SCENARIO: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"{'='*80}\n")
        
        # Run the scenario through the orchestrator
        result = GEMMA_ORCHESTRATOR(
            cv_output=scenario['cv_output'],
            sensor_data=scenario['sensor_data'],
            location_name=scenario['location']
        )
        
        # Display results
        print("INPUT DATA:")
        print(f"  Location: {scenario['location']}")
        print(f"  Coral Health: {scenario['cv_output']['health']} ({scenario['cv_output']['confidence']:.0%} confidence)")
        print(f"  Water Temp: {scenario['sensor_data']['water_temp_c']}°C")
        print(f"  pH: {scenario['sensor_data']['ph_level']}")
        print(f"  Turbidity: {scenario['sensor_data']['turbidity_ntu']} NTU")
        print()
        
        print("AI RECOMMENDATION:")
        print(f"  Alert Level: {result['alert_level']}")
        print(f"  Recommended Technique: {result['technique_name']}")
        print(f"  Predicted Survival: {result['predicted_survival_rate']}")
        print(f"  Cost: {result['estimated_cost_per_hectare']}")
        print(f"  Confidence: {result['confidence_score']:.0%}")
        print()
        
        print("REASONING:")
        print(f"  {result['reasoning']}")
        print()
        
        print("RISK FACTORS:")
        for risk in result['risk_factors']:
            print(f"  • {risk}")
        print()
        
        print("NEXT STEPS:")
        for step in result['next_steps']:
            print(f"  {step}")
        print()
        
        # Verify expected outputs
        expected_technique = scenario['expected_recommendation']
        expected_alert = scenario['expected_alert']
        actual_technique = result['recommended_technique']
        actual_alert = result['alert_level']
        
        technique_match = actual_technique == expected_technique
        alert_match = actual_alert == expected_alert
        
        if technique_match and alert_match:
            print("✅ TEST PASSED")
            passed += 1
        else:
            print("❌ TEST FAILED")
            if not technique_match:
                print(f"   Expected technique: {expected_technique}")
                print(f"   Actual technique: {actual_technique}")
            if not alert_match:
                print(f"   Expected alert: {expected_alert}")
                print(f"   Actual alert: {actual_alert}")
            failed += 1
        
        print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Scenarios: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Your system is ready for the demo!")
    else:
        print(f"⚠️  {failed} test(s) failed. Review the outputs above.")
    
    return failed == 0


if __name__ == "__main__":
    success = test_all_scenarios()
    exit(0 if success else 1)