
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([

        # 1. Start Turtlesim
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim'
        ),

        # 2. Start GoToPose Action Server
        Node(
            package='turtle_controller',
            executable='go_to_pose_server',
            name='go_to_pose_server',
            parameters=[{
                'max_linear_speed': 1.5,
                'max_angular_speed': 1.5
            }]
        ),

        # 3. Start Reset Service
        Node(
            package='turtle_controller',
            executable='reset_server',
            name='reset_server'
        ),

        # 4. Start Square Action Server
        Node(
            package='turtle_controller',
            executable='square_server',
            name='square_server'
        )

    ])
