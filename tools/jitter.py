import json
import random
import os

def calculate_jitter(current_activity, volatility=0.15):
    """
    Simulates cognitive jitter using a simple random walk 
    with a tendency to return to a baseline (mean reversion).
    """
    # Baseline activity level
    baseline = 0.5 
    # Brownian-like motion: random shift + mean reversion
    drift = (baseline - current_activity) * 0.1
    noise = random.uniform(-volatility, volatility)
    
    new_activity = current_activity + drift + noise
    # Clamp between 0.0 and 1.0
    return max(0.0, min(1.0, new_activity))

def update_state():
    state_path = 'state/current-state.json'
    if not os.path.exists(state_path):
        print("State file not found.")
        return

    with open(state_path, 'r') as f:
        state = json.load(f)

    current_act = state.get('activity', 0.5)
    new_act = calculate_jitter(current_act)
    
    state['activity'] = round(new_act, 4)
    
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"Cognitive Jitter applied: {current_act} -> {state['activity']}")

if __name__ == "__main__":
    update_state()
