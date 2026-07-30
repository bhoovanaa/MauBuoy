from roi_calculator import calculate_restoration_roi
from environmental_stress import calculate_environmental_stress

# Test 1: Blue Bay scenario
stress = calculate_environmental_stress(29.8, 8.1, 2.1, 35.2)
print(f"Stress: {stress}")  # Should show HIGH stress due to temp

roi = calculate_restoration_roi("heat_resistant_outplanting", "bleached", stress["stress_score"])
print(f"ROI: {roi}")  # Should show ~82% survival, $30k cost