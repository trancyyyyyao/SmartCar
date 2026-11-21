import math 
from pathlib import Path
import rclpy
import yaml
from geometry_msgs.msg import TransformStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from tf2_ros import StaticTransformBroadcaster

def quaternion_from_rpy(roll,pitch,yaw):
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    qx = sr * cp * cy - cr * sp * sy
    qy = cr * sp * cy + sr * cp * sy
    qz = cr * cp * sy - sr * sp * cy
    qw = cr * cp * cy + sr * sp * sy
    return qx, qy, qz, qw

def read_xyz(config,field_name):
    value=config.get(field_name)
    if not isinstance(value,list) or len(value)!=3:
        raise ValueError(f"{field_name} 必须是包含三个数值的列表")
    return tuple(float(item) for item in value)

def read_rpy(config):
    value=config.get("rpy",[0.0,0.0,0.0])
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError("rpy 必须是包含三个数值的列表")
    return tuple(float(item) for item in value)

class StaticTfNode(Node):
    def __init__(self):
        super().__init__("static_tf_node")
        self.declare_parameter("extrinsics_file","extrinsics.yaml")
        file_value=self.get_parameter("extrinsics_file").value
        extrinsics_path = Path(file_value).expanduser()

        if not extrinsics_path.is_file():
            raise RuntimeError( f"外参文件不存在: {extrinsics_path}")

        try:
            with extrinsics_path.open(
                "r",
                encoding="utf-8",
            )as stream:
                config=yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise RuntimeError( f"外参 YAML 解析失败: {exc}")from exc

        if not isinstance(config,dict):
            raise RuntimeError( f"外参 YAML 内容不是字典: {extrinsics_path}")

        frames=config.get("frames",{})
        laser_config=config.get("laser_link",{})
        camera_config=config.get("camera_link",{})
        map_frame=str(frames.get("map","map"))
        odom_frame=str(frames.get("odom","odom"))
        base_frame=str(frames.get("base_link","base_link"))
        laser_parent=str(laser_config.get("parent",base_frame))
        laser_child=str(frames.get("laser_link","laser_link"))
        camera_parent=str(camera_config.get("parent",base_frame))
        camera_child=str(frames.get("camera_link","camera_link"))
        if laser_parent!=base_frame:
            raise ValueError(f"laser_link 的 parent 应为 {base_frame},"f"实际为 {laser_parent}")
        if camera_parent!=base_frame:
            raise ValueError(f"camera_link 的 parent 应为 {base_frame},"f"实际为 {camera_parent}")

        laser_xyz=read_xyz(laser_config,"xyz")
        laser_rpy=read_rpy(laser_config)
        camera_xyz=read_xyz(camera_config,"xyz")
        camera_rpy=read_rpy(camera_config)
        stamp = self.get_clock().now().to_msg()

        transforms=[
            self.make_transform(parent=map_frame,child=odom_frame,xyz=(0.0, 0.0, 0.0),rpy=(0.0, 0.0, 0.0),stamp=stamp,),
            self.make_transform(parent=odom_frame,child=base_frame,xyz=(0.0, 0.0, 0.0),rpy=(0.0, 0.0, 0.0),stamp=stamp,),
            self.make_transform(parent=laser_parent,child=laser_child,xyz=laser_xyz,rpy=laser_rpy,stamp=stamp,),
            self.make_transform(parent=camera_parent,child=camera_child,xyz=camera_xyz,rpy=camera_rpy,stamp=stamp,),
        ]
        self.broadcaster = StaticTransformBroadcaster(self)
        self.broadcaster.sendTransform(transforms)
        self.get_logger().info(f"已从 {extrinsics_path} 发布静态 TF")  
        self.get_logger().info(f"{map_frame} -> {odom_frame} -> {base_frame}")  
        self.get_logger().info(f"{laser_parent} -> {laser_child}, xyz={laser_xyz}, " f"rpy={laser_rpy}")  
        self.get_logger().info(f"{camera_parent} -> {camera_child}, xyz={camera_xyz}, "f"rpy={camera_rpy}")  


    def make_transform(self,parent,child,xyz,rpy,stamp):
        transform=TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = parent
        transform.child_frame_id = child
        transform.transform.translation.x = xyz[0]
        transform.transform.translation.y = xyz[1]
        transform.transform.translation.z = xyz[2]
        qx, qy, qz, qw = quaternion_from_rpy(*rpy)
        transform.transform.rotation.x = qx
        transform.transform.rotation.y = qy
        transform.transform.rotation.z = qz
        transform.transform.rotation.w = qw
        return transform



def main(args=None):
    rclpy.init(args=args)
    node=None
    try:
        node=StaticTfNode()
        rclpy.spin(node)
    except(KeyboardInterrupt,ExternalShutdownException,):
        pass
    except Exception as exc:
        logger=rclpy.logging.get_logger("static_tf_node")
        logger.error(str(exc))
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()



if __name__=="__main__":
    main()

