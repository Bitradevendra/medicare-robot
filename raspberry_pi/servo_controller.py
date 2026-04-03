# ============================================================
#  Medicare Robot - Servo Motor Controller
#  Controls SG90 servo for medicine box selection
# ============================================================

import time

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("[WARN] RPi.GPIO not available - running in simulation mode")
    GPIO = None

from config import (
    SERVO_PIN, SERVO_FREQUENCY,
    SERVO_BOX_1, SERVO_BOX_2, SERVO_BOX_3
)


class ServoController:
    """Controls a servo motor for medicine box dispensing."""

    def __init__(self):
        self.current_angle = 0
        self.pwm = None

        if GPIO:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(SERVO_PIN, GPIO.OUT)
            self.pwm = GPIO.PWM(SERVO_PIN, SERVO_FREQUENCY)
            self.pwm.start(0)
            print(f"[SERVO] Initialized on GPIO {SERVO_PIN}")
        else:
            print("[SERVO] Running in simulation mode")

    def _angle_to_duty_cycle(self, angle):
        """Convert angle (0-180) to duty cycle (2.5-12.5)."""
        angle = max(0, min(180, angle))
        return 2.5 + (angle / 180.0) * 10.0

    def set_angle(self, angle):
        """Move servo to a specific angle."""
        duty_cycle = self._angle_to_duty_cycle(angle)
        self.current_angle = angle

        if self.pwm:
            self.pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(0.5)  # Wait for servo to reach position
            self.pwm.ChangeDutyCycle(0)  # Stop jitter
        
        print(f"[SERVO] Moved to {angle}° (duty: {duty_cycle:.1f}%)")

    def go_to_box(self, box_number):
        """Move servo to the specified box position."""
        box_angles = {
            1: SERVO_BOX_1,   # 0 degrees
            2: SERVO_BOX_2,   # 30 degrees
            3: SERVO_BOX_3,   # 60 degrees
        }

        if box_number in box_angles:
            angle = box_angles[box_number]
            print(f"[SERVO] Moving to Box {box_number} ({angle}°)")
            self.set_angle(angle)
            return True
        else:
            print(f"[SERVO] Invalid box number: {box_number}")
            return False

    def sweep_test(self):
        """Test servo by sweeping through all box positions."""
        print("[SERVO] Running sweep test...")
        for box in [1, 2, 3]:
            self.go_to_box(box)
            time.sleep(1)
        self.set_angle(0)
        print("[SERVO] Sweep test complete")

    def cleanup(self):
        """Clean up GPIO resources."""
        if self.pwm:
            self.pwm.stop()
        print("[SERVO] Cleaned up")


if __name__ == "__main__":
    servo = ServoController()
    try:
        servo.sweep_test()
    finally:
        servo.cleanup()
        if GPIO:
            GPIO.cleanup()
