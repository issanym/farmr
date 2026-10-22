import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    bringup_share = get_package_share_directory('bringup')
    desc_share = get_package_share_directory('farmr_description')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    # Arguments
    use_rviz = LaunchConfiguration('use_rviz')
    world = LaunchConfiguration('world')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')

    declare_args = [
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument(
            'world',
            default_value=os.path.join(bringup_share, 'worlds', 'world.sdf'),
            description='Path to the Gazebo world file'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('z', default_value='0.2'),
    ]

    # Let Gazebo resolve model:// and package:// meshes
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.dirname(desc_share) + os.pathsep +
              os.environ.get('GZ_SIM_RESOURCE_PATH', ''),
    )

    # Robot description from the sim xacro
    robot_description = ParameterValue(
        Command([
            'xacro ',
            os.path.join(desc_share, 'urdf', 'farmr_sim.urdf.xacro'),
        ]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
        }],
    )

    # Gazebo server + GUI, run immediately (-r)
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': ['-r -v 2 ', world]}.items(),
    )

    # Spawn the robot from the robot_description topic
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'farmr',
            '-x', x, '-y', y, '-z', z,
        ],
    )

    # ROS <-> Gazebo bridge (adjust to match plugins in your xacro)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            #'/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
        ],
        parameters=[{'use_sim_time': True}],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        output='screen',
        parameters=[{'use_sim_time': True}],
        condition=IfCondition(use_rviz),
        # add: arguments=['-d', os.path.join(bringup_share, 'rviz', 'sim.rviz')]
        # once you save an rviz config
    )

    return LaunchDescription([
        *declare_args,
        set_gz_resource_path,
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
        rviz,
    ])
