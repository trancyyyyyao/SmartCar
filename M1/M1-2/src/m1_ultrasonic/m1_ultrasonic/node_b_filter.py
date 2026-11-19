import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32


from sensor_interfaces.msg import SensorData

class FilterNode(Node):
    def __init__(self):
        super().__init__("node_b_filter")
        self.declare_parameter("alpha",0.3)
        self.previous_output=None

        self.subscription=self.create_subscription(
            SensorData,
            "sensor_data",
            self.on_sensor_data,
            10,
        )
        self.publisher=self.create_publisher(
            Float32,
            "processed_distance",
            10,
        )
        self.get_logger().info("节点 B 已启动，等待传感器数据")


    def on_sensor_data(self,msg):
         if msg.status != 0:
            self.get_logger().warning(
                f"[WARN] 丢弃无效数据: status={msg.status}"
            )
            return
         current_value = float(msg.distance)
         alpha = float(self.get_parameter("alpha").value)
         if alpha < 0.0 or alpha > 1.0:
            self.get_logger().warning(
                f"[WARN] alpha={alpha} 超出范围，应为 0.0～1.0"
            )
            return
         if self.previous_output is None:
            filtered_value = current_value
         else:
            filtered_value=alpha*current_value+(1-alpha)*self.previous_output
         self.previous_output = filtered_value   
         output_msg = Float32()
         output_msg.data = float(filtered_value)
         self.publisher.publish(output_msg)



def main(args=None):
    rclpy.init(args=args)
    node = FilterNode()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()



if __name__=="__main__":
    main()