
import os
from launch import LaunchDescription
from launch.actions import(
    DeclareLaunchArgument,
    GroupAction,
    OpaqueFunction,
    RegisterEventHandler,
    TimerAction,
    LogInfo,
    Shutdown,
)
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node,PushRosNamespace

def launch_setup(context,*args,**kwargs):
    del args,kwargs
    namespace=LaunchConfiguration("namespace").perform(context)
    params_file=LaunchConfiguration("params_file").perform(context)
    use_sim_time_text=LaunchConfiguration("use_sim_time").perform(context)
    use_sim_time=use_sim_time_text.lower()=="true"

    if params_file and not os.path.isfile(params_file):
        error_message = f"[ERROR] 参数文件不存在: {params_file}"
        return [
            LogInfo(msg=error_message),
            Shutdown(reason=error_message),
        ]
    parameters=[{"use_sim_time":use_sim_time},]
    if params_file:
        parameters.insert(0,params_file)

    node_a=Node(
        package="m1_ultrasonic",
        executable="node_a_sensor",
        name="node_a_sensor",
        output="screen",
        parameters=parameters,
    )
    node_b=Node(
        package="m1_ultrasonic",
        executable="node_b_filter",
        name="node_b_filter",
        output="screen",
        parameters=parameters,
    )
    node_c=Node(
        package="m1_ultrasonic",
        executable="node_c_alarm",
        name="node_c_alarm",
        output="screen",
        parameters=parameters,
    )
    start_node_c=GroupAction(
        actions=[
            PushRosNamespace(namespace),
            node_c,
        ]
    )
    start_c_after_b=RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=node_b,
            on_start=[
                TimerAction(
                    period=1.0,
                    actions=[start_node_c]
                )
            ],
        )
    )
    return[
        GroupAction(
            actions=[
                PushRosNamespace(namespace),
                node_a,
                node_b,
                start_c_after_b,
            ]
        )
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "namespace",
                default_value="robot1",
                description="三个节点共用的命名空间",
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value="",
                description="YAML文件路径",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="false",
               description="是否使用仿真时间",
            ),
            OpaqueFunction(function=launch_setup)
        ]

    )
