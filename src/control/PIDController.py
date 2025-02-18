
import time 
class PIDController:
    """this class implements a PID controller for lane following"""
    def __init__(self, Kp=0.9, Ki=0, Kd=0.01, setangle=90):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setangle = setangle
        self.previous_error = 0
        self.integral = 0
        self.previous_time=time.time()


    def compute(self, steering_angle):
          dt=time.time() - self.previous_time
          error = steering_angle - self.setangle
     
          P_out = self.Kp * error
     
          self.integral += error * dt
          I_out = self.Ki * self.integral
          
          derivative = (error - self.previous_error) / dt
          D_out = self.Kd * derivative
          
          output = P_out + I_out + D_out
          if output>21:
               output=21
          elif output<-21:
               output=-21
          self.previous_error = error

         # print('output from the pid is: ',output)
          self.previous_time=time.time()
          
          return output


    