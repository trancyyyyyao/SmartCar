import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from sensor_interfaces.srv import TriggerAlarm

class AlarmServer(Node):
    def __init__(self):
        super().__init__("alarm_server")
        self.server=self.create_service(
            TriggerAlarm,
            "trigger_alarm",
            self.on_trigger_alarm,
        )
        self.get_logger().info("报警服务端已启动")


    def on_trigger_alarm(self,request,response):
        del request
        self.get_logger().info("[ALARM] 距离过近！")
        response.success = True
        response.message = "alarm triggered"
        return response


def main(args=None):
    rclpy.init(args=args)
    node = AlarmServer()

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
