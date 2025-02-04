
class PIDController:
    """this class implements a PID controller for lane following"""
    def __init__(self, Kp=1, Ki=0, Kd=0, setangle=90):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setangle = setangle
        self.previous_error = 0
        self.integral = 0

def compute(self, steering_angle, dt):
        error = steering_angle - self.setangle
    
        P_out = self.Kp * error
 
        self.integral += error * dt
        I_out = self.Ki * self.integral
        
        derivative = (error - self.previous_error) / dt
        D_out = self.Kd * derivative
        
        output = P_out + I_out + D_out
        self.previous_error = error
        
        return output


    