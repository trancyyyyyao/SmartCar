import math 
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from sensor_interfaces.msg import SensorData
PUBLISH_HZ = 10.0

class SensorNode(Node):
    def __init__(self):
        super().__init__("node_a_sensor")
        self.publisher=self.create_publisher(
            SensorData,
            "sensor_data",
            10,
        )

        self.timer=self.create_timer(
            1.0/PUBLISH_HZ,
            self.on_timer,
        )
        self.sample_index=0
        self.get_logger().info("节点 A 已启动，以 10 Hz 发布传感器数据")


    def simulate_reading(self):
        index=self.sample_index
        distance=0.8+0.6*math.sin(index*0.2)

        status=0
        if index%20==10:
            status=1
        elif index % 31 == 15:
            status=2
     
        return distance,status


    def on_timer(self):
        
        distance, status = self.simulate_reading()
        msg = SensorData()
        msg.distance = float(distance)
        msg.unit = "m"
        msg.stamp = self.get_clock().now().to_msg()
        msg.status = int(status)
        self.publisher.publish(msg)
        self.sample_index += 1


def main(args=None):
    rclpy.init(args=args)
    node = SensorNode()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
    