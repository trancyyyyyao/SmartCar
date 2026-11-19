import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32

from sensor_interfaces.srv import TriggerAlarm

class AlarmClientNode(Node):
    def __init__(self):
        super().__init__("node_c_alarm")
        self.declare_parameter("alarm_threshold",0.3)
        self.declare_parameter("service_timeout",1.0)

        self.previous_below_threshold=False
        self.active_future=None
        self.timeout_timer=None

        self.subscription=self.create_subscription(
            Float32,
            "processed_distance",
            self.on_distance,
            10,
        )
        self.client=self.create_client(
            TriggerAlarm,
            "trigger_alarm",
        )
        self.get_logger().info("节点 C 已启动，等待滤波距离")


    def on_distance(self,msg):
        distance=float(msg.data)
        threshold = float(
            self.get_parameter("alarm_threshold").value
        )
        if threshold <= 0.0:
            self.get_logger().warning(
                f"[WARN] alarm_threshold={threshold} 必须大于 0"
            )
            return
        
        current_below = distance < threshold
        should_trigger = (
            current_below
            and not self.previous_below_threshold
        )
        self.previous_below_threshold = current_below
        if not should_trigger:
            return
        if self.active_future is not None:
            self.get_logger().warning(
                "[WARN] 上一次报警请求尚未结束"
            )
            return
        self.start_alarm_request(distance)


    def start_alarm_request(self,distance):
        timeout=float(self.get_parameter("service_timeout").value)
        if timeout <= 0.0:
            self.get_logger().warning(
                f"[WARN] service_timeout={timeout} 必须大于 0"
            )
            return
        request=TriggerAlarm.Request()
        future = self.client.call_async(request)

        self.active_future = future
        self.get_logger().info( 
            f"距离 {distance:.3f} m 低于阈值，请求报警"
        )
        future.add_done_callback(
            self.on_service_response
        )
        self.timeout_timer = self.create_timer(
            timeout,
            self.on_service_timeout,
        )


    def on_service_response(self, future):
        if future is not self.active_future:
            return
        self.cancel_timeout_timer()
        try:
            response = future.result()
        except Exception as exc:
            self.get_logger().error(
                f"报警服务调用失败: {exc}"
            )
        else:
            if response is None:
                self.get_logger().warning(
                    "[WARN] 报警服务没有返回响应"
                )
            else:
                self.get_logger().info(
                    "报警响应: "
                    f"success={response.success}, "
                    f"message={response.message}"
                )
        finally:
            self.active_future = None


    def on_service_timeout(self):
        self.get_logger().warning("[WARN] 报警服务超时")
        future = self.active_future
        self.active_future = None
        self.cancel_timeout_timer()
        if future is not None:
            future.cancel()


    def cancel_timeout_timer(self):
        timer = self.timeout_timer
        if timer is None:
            return
        self.timeout_timer = None
        timer.cancel()
        timer.destroy()



def main(args=None):
    rclpy.init(args=args)
    node = AlarmClientNode()

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