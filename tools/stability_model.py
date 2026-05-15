import numpy as np

class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint=0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        
        self._prev_error = 0
        self._integral = 0
        self._last_time = None

    def update(self, measurement, current_time):
        if self._last_time is None:
            self._last_time = current_time
            return 0

        dt = current_time - self._last_time
        if dt <= 0: return 0

        error = self.setpoint - measurement
        
        # Proportional term: Corrects based on present error
        Pout = self.Kp * error
        
        # Integral term: Corrects based on accumulated historical error (bias)
        self._integral += error * dt
        Iout = self.Ki * self._integral
        
        # Derivative term: Predicts future error by rate of change (damping)
        derivative = (error - self._prev_error) / dt
        Dout = self.Kd * derivative
        
        output = Pout + Iout + Dout
        
        self._prev_error = error
        self._last_time = current_time
        
        return output

def simulate_system(controller, iterations=50, dt=1.0):
    current_value = 0.0 # Start at zero
    history = []
    plant_gain = 0.1 
    for i in range(iterations):
        t = i * dt
        u = controller.update(current_value, t)
        current_value += u * plant_gain
        history.append(round(current_value, 4))
    return history

if __name__ == "__main__":
    print("--- PID Stability Simulation ---")
    
    # Underdamped/Oscillating settings
    pid_under = PIDController(Kp=2.5, Ki=0.5, Kd=0.1, setpoint=10)
    val_under = simulate_system(pid_under)
    
    # Stable approach settings
    pid_stable = PIDController(Kp=1.2, Ki=0.1, Kd=0.8, setpoint=10)
    val_stable = simulate_system(pid_stable)
    
    print("\nSetpoint: 10.0")
    print("\n[Case A: Under-tuned / High Gain]")
    print("Cycle | Value | Gap")
    for i, v in enumerate(val_under):
        print(f"{i:5} | {v:5.2f} | {10-v:5.2f}")
    
    print("\n[Case B: Critically Damped / Balanced]")
    print("Cycle | Value | Gap")
    for i, v in enumerate(val_stable):
        print(f"{i:5} | {v:5.2f} | {10-v:5.2f}")
    
    print("\nSummary:")
    print(f"Under-tuned Final Val: {val_under[-1]}")
    print(f"Stable Final Val:      {val_stable[-1]}")
