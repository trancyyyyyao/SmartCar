import math 
import numpy as np
import statistics
import rclpy
from message_filters import (ApproximateTimeSynchronizer,Subscriber)
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from sensor_msgs.msg import Image,LaserScan
from rclpy.duration import Duration
from tf2_ros import(Buffer,TransformListener,TransformException,)
def stamp_to_seconds(stamp):
    return stamp.sec+stamp.nanosec/1e9


def scan_to_points(scan_msg):
     ranges=np.asarray(scan_msg.ranges,dtype=np.float64,)
     if ranges.size==0:
          return (np.empty((0, 3), dtype=np.float64),np.empty((0,), dtype=np.float64),)
     angles=(scan_msg.angle_min+np.arange(ranges.size,dtype=np.float64)*scan_msg.angle_increment)
     valid_mask=(np.isfinite(ranges)& (ranges >= scan_msg.range_min)& (ranges <= scan_msg.range_max))
     valid_ranges = ranges[valid_mask]
     valid_angles = angles[valid_mask]
     points = np.zeros((valid_ranges.size, 3),dtype=np.float64,)
     points[:, 0] = valid_ranges * np.cos(valid_angles)
     points[:, 1] = valid_ranges * np.sin(valid_angles)
     points[:, 2] = 0.0
     return points, valid_ranges


def quaternion_to_rotation_matrix(x,y,z,w,):
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if norm < 1e-12:
        raise ValueError("四元数模长接近 0")
    x /= norm
    y /= norm
    z /= norm
    w /= norm
    xx = x * x
    yy = y * y
    zz = z * z
    xy = x * y
    xz = x * z
    yz = y * z
    wx = w * x
    wy = w * y
    wz = w * z
    return np.array(
        [
            [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
            [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
            [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
        ],
        dtype=np.float64,
    )


def transform_points(points, transform):
    rotation = quaternion_to_rotation_matrix(
        transform.rotation.x,
        transform.rotation.y,
        transform.rotation.z,
        transform.rotation.w,
    )
    translation = np.array(
        [
            transform.translation.x,
            transform.translation.y,
            transform.translation.z,
        ],
        dtype=np.float64,
    )
    return points @ rotation.T + translation  



class ProjectionNode(Node):
    def __init__(self):
        super().__init__("projection_node")

        self.declare_parameter("sync_slop", 0.02)
        self.declare_parameter("queue_size", 50)
        self.declare_parameter("camera_frame", "camera_link")

        self.sync_slop=float(self.get_parameter("sync_slop").value)
        self.queue_size=int(self.get_parameter("queue_size").value)
        self.camera_frame = str(self.get_parameter("camera_frame").value)
       
        if self.sync_slop<=0.0:
            raise ValueError(f"sync_slop的值应该大于零但实际上sync_slop的值为{self.sync_slop}")
        if self.queue_size<2:
            raise ValueError(f"queue_size的值应该大于零但实际上queue_size的值为{self.queue_size}")
        
        self.pair_count=0
        self.delta_ms_values = []
        self.transform_error_count = 0
        self.total_valid_points = 0

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(
            self.tf_buffer,
            self,
        )
        self.scan_sub=Subscriber(self,LaserScan,"/scan",)
        self.image_sub=Subscriber(self,Image,"/camera/image_raw",)
        self.synchronizer=ApproximateTimeSynchronizer(
            [self.scan_sub, self.image_sub],
            queue_size=self.queue_size,
            slop=self.sync_slop,
        )
        self.synchronizer.registerCallback(self.on_synced)
        self.report_timer=self.create_timer(1.0,self.report_summary,)
        self.get_logger().info(
            f"同步节点已启动: slop={self.sync_slop:.3f}s, "
            f"queue_size={self.queue_size}"
        )

    def on_synced(self,scan_msg,image_msg):
            scan_time=stamp_to_seconds(scan_msg.header.stamp)
            image_time = stamp_to_seconds(image_msg.header.stamp)
            delta_ms = abs(scan_time - image_time) * 1000.0
            self.pair_count += 1
            self.delta_ms_values.append(delta_ms)
            points_laser, valid_ranges = scan_to_points(scan_msg)
            if points_laser.size == 0:
                self.get_logger().warning("当前激光帧没有有效点")
                return
            self.total_valid_points += points_laser.shape[0]
            source_frame = scan_msg.header.frame_id
            if not source_frame:
                source_frame = "laser_link"
            try:
                stamped_transform = self.tf_buffer.lookup_transform(
                self.camera_frame,
                source_frame,
                scan_msg.header.stamp,
                timeout=Duration(seconds=0.1),
            )
            except TransformException as exc:
                self.transform_error_count += 1
                self.get_logger().warning(
                    f"TF 查询失败: "
                    f"{self.camera_frame} <- {source_frame}: {exc}"
                )
                return
            points_camera = transform_points(points_laser,stamped_transform.transform,)
            camera_x = points_camera[:, 0]
            camera_y = points_camera[:, 1]
            camera_z = points_camera[:, 2]
            
            self.get_logger().info(
            f"sync count={self.pair_count} "
            f"dt_ms={delta_ms:.3f} "
            f"valid_points={points_camera.shape[0]} "
            f"range=[{valid_ranges.min():.3f}, "
            f"{valid_ranges.max():.3f}] "
            f"camera_x=[{camera_x.min():.3f}, "
            f"{camera_x.max():.3f}] "
            f"camera_y=[{camera_y.min():.3f}, "
            f"{camera_y.max():.3f}] "
            f"camera_z=[{camera_z.min():.3f}, "
            f"{camera_z.max():.3f}]"
            )

    def report_summary(self):
            if not self.delta_ms_values:
                return 
            median_ms=statistics.median(self.delta_ms_values)
            average_points = (
                self.total_valid_points / self.pair_count
                if self.pair_count
                else 0.0
            )
            self.get_logger().info(
                f"summary: count={self.pair_count}, "
                f"median_dt_ms={median_ms:.3f}, "
                f"transform_errors={self.transform_error_count}, "
                f"average_points={average_points:.1f}"
            )



def main(args=None):
    rclpy.init(args=args)
    node=None
    try:
        node=ProjectionNode()
        rclpy.spin(node)
    except(KeyboardInterrupt,ExternalShutdownException):pass
    except Exception as exc:
        logger=rclpy.logging.get_logger("projection_node")
        logger.error(str(exc))
    finally:
        if node is not None:
            node.report_summary()
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__=="__main__":
    main()
        
        
