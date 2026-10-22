import math

import rclpy
import tf2_ros
from geometry_msgs.msg import Quaternion, TransformStamped
from gpiozero import RotaryEncoder
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import JointState

class Encoders(Node):
    def __init__(self):
        super().__init__('encoders')
        self.left_wheel = RotaryEncoder()
        self.right_wheel = RotaryEncoder()

def main(args=None):
    rclpy.init(args=args)
    enc_node= Encoders()
    rclpy.spin(enc_node)
    enc_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
