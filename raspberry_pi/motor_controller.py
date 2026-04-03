# ============================================================
#  Medicare Robot - DC Motor Controller
#  Controls 2 DC motors via L298N motor driver for movement
#  EN pins are jumpered HIGH on L298N = always full speed
# ============================================================

import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("[WARN] RPi.GPIO not available - running in simulation mode")
    GPIO = None

from config import (
    MOTOR_A_IN1, MOTOR_A_IN2,
    MOTOR_B_IN1, MOTOR_B_IN2,
)


class MotorController:
    """Controls two DC motors via L298N H-Bridge motor driver.
    
    EN (enable) pins are physically jumpered HIGH on the L298N board,
    so motors always run at full speed. Only direction is controlled.
    """

    def __init__(self):
        self.is_moving = False
        self.current_action = "stopped"

        if GPIO:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)

            # Motor A (Left) direction pins
            GPIO.setup(MOTOR_A_IN1, GPIO.OUT)
            GPIO.setup(MOTOR_A_IN2, GPIO.OUT)

            # Motor B (Right) direction pins
            GPIO.setup(MOTOR_B_IN1, GPIO.OUT)
            GPIO.setup(MOTOR_B_IN2, GPIO.OUT)

            print("[MOTORS] Initialized L298N motor driver (full speed, no EN pins)")
        else:
            print("[MOTORS] Running in simulation mode")

    def _set_motor_a(self, forward=True):
        """Set Motor A (Left wheel) direction."""
        if GPIO:
            if forward:
                GPIO.output(MOTOR_A_IN1, GPIO.HIGH)
                GPIO.output(MOTOR_A_IN2, GPIO.LOW)
            else:
                GPIO.output(MOTOR_A_IN1, GPIO.LOW)
                GPIO.output(MOTOR_A_IN2, GPIO.HIGH)

    def _set_motor_b(self, forward=True):
        """Set Motor B (Right wheel) direction."""
        if GPIO:
            if forward:
                GPIO.output(MOTOR_B_IN1, GPIO.HIGH)
                GPIO.output(MOTOR_B_IN2, GPIO.LOW)
            else:
                GPIO.output(MOTOR_B_IN1, GPIO.LOW)
                GPIO.output(MOTOR_B_IN2, GPIO.HIGH)

    def _stop_motor_a(self):
        """Stop Motor A."""
        if GPIO:
            GPIO.output(MOTOR_A_IN1, GPIO.LOW)
            GPIO.output(MOTOR_A_IN2, GPIO.LOW)

    def _stop_motor_b(self):
        """Stop Motor B."""
        if GPIO:
            GPIO.output(MOTOR_B_IN1, GPIO.LOW)
            GPIO.output(MOTOR_B_IN2, GPIO.LOW)

    def move_forward(self):
        """Move robot forward - both motors forward at full speed."""
        self._set_motor_a(forward=True)
        self._set_motor_b(forward=True)
        self.is_moving = True
        self.current_action = "forward"
        print("[MOTORS] Moving FORWARD (full speed)")

    def move_backward(self):
        """Move robot backward at full speed."""
        self._set_motor_a(forward=False)
        self._set_motor_b(forward=False)
        self.is_moving = True
        self.current_action = "backward"
        print("[MOTORS] Moving BACKWARD (full speed)")

    def turn_left(self):
        """Turn left - right motor forward, left motor stopped."""
        self._stop_motor_a()              # Stop left wheel
        self._set_motor_b(forward=True)   # Right wheel forward
        self.is_moving = True
        self.current_action = "turning_left"
        print("[MOTORS] Turning LEFT")

    def turn_right(self):
        """Turn right - left motor forward, right motor stopped."""
        self._set_motor_a(forward=True)   # Left wheel forward
        self._stop_motor_b()              # Stop right wheel
        self.is_moving = True
        self.current_action = "turning_right"
        print("[MOTORS] Turning RIGHT")

    def spin_left(self):
        """Spin in place to the left."""
        self._set_motor_a(forward=False)
        self._set_motor_b(forward=True)
        self.is_moving = True
        self.current_action = "spinning_left"
        print("[MOTORS] Spinning LEFT")

    def spin_right(self):
        """Spin in place to the right."""
        self._set_motor_a(forward=True)
        self._set_motor_b(forward=False)
        self.is_moving = True
        self.current_action = "spinning_right"
        print("[MOTORS] Spinning RIGHT")

    def stop(self):
        """Stop all motors immediately."""
        self._stop_motor_a()
        self._stop_motor_b()
        self.is_moving = False
        self.current_action = "stopped"
        print("[MOTORS] STOPPED")

    def get_status(self):
        """Get current motor status."""
        return {
            "is_moving": self.is_moving,
            "action": self.current_action,
        }

    def cleanup(self):
        """Clean up GPIO resources."""
        self.stop()
        print("[MOTORS] Cleaned up")


if __name__ == "__main__":
    motors = MotorController()
    try:
        print("Testing motors...")
        motors.move_forward()
        time.sleep(2)
        motors.turn_left()
        time.sleep(1)
        motors.turn_right()
        time.sleep(1)
        motors.stop()
    finally:
        motors.cleanup()
        if GPIO:
            GPIO.cleanup()
