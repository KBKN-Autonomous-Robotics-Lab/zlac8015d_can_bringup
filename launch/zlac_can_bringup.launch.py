import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_name = 'zlac_can_bringup'
    urdf_file = os.path.join(get_package_share_directory(pkg_name), 'urdf', 'orange_go_2025.urdf')
    controller_config_file = os.path.join(get_package_share_directory(pkg_name), 'config', 'controllers.yaml')

    with open(urdf_file, 'r') as infp:
        robot_description_content = infp.read()

    # Robot State Publisher (必須)
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description_content}]
    )

    # Controller Manager (ros2_control_node)
    # ここで robot_description をパラメータとして渡さないと、
    # hardware_interface の on_activate が呼ばれません。
    controller_manager_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[{'robot_description': robot_description_content}, controller_config_file],
        remappings=[
            ('/diff_drive_controller/cmd_vel_unstamped', '/cmd_vel'),
            ('/diff_drive_controller/odom', '/odom'),
        ],
        output='both',
    )

    # Spawner (broadcaster と diff_drive_controller)
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
    )

    diff_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller', '--controller-manager', '/controller_manager'],
    )

    return LaunchDescription([
        robot_state_publisher_node,
        controller_manager_node,
        joint_state_broadcaster_spawner,
        diff_drive_controller_spawner
    ])
