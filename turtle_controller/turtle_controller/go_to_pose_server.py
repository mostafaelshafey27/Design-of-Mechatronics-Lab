import math
import time
import threading

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.parameter import Parameter

from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtle_interfaces.action import GoToPose
from turtle_interfaces.srv import SetSpeedLimits


class GoToPoseServer(Node):

    def __init__(self):
        super().__init__('go_to_pose_server')

        self.group = ReentrantCallbackGroup()
        self.current_pose = None
        self.goal_lock = threading.Lock()
        self.busy = False

        # Speed parameters
        self.declare_parameter('max_linear_speed', 1.5)
        self.declare_parameter('max_angular_speed', 1.5)

        # Read turtle position
        self.pose_sub = self.create_subscription(
            Pose, '/turtle1/pose',
            self.pose_callback, 10,
            callback_group=self.group
        )

        # Send velocity commands
        self.vel_pub = self.create_publisher(
            Twist, '/turtle1/cmd_vel', 10
        )

        # Speed service
        self.speed_service = self.create_service(
            SetSpeedLimits,
            'set_speed_limits',
            self.set_speed_callback,
            callback_group=self.group
        )

        # GoToPose action server
        self.action_server = ActionServer(
            self,
            GoToPose,
            'go_to_pose',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.group
        )

        self.get_logger().info(
            'GoToPose Action Server is ready!'
        )

    def pose_callback(self, msg):
        self.current_pose = msg

    def set_speed_callback(self, request, response):
        linear = request.max_linear_speed
        angular = request.max_angular_speed

        if not (math.isfinite(linear) and math.isfinite(angular)):
            response.success = False
            response.message = 'Speeds must be finite!'
            return response

        if linear <= 0 or angular <= 0:
            response.success = False
            response.message = 'Speeds must be positive!'
            return response

        results = self.set_parameters([
            Parameter(
                'max_linear_speed',
                Parameter.Type.DOUBLE,
                linear
            ),
            Parameter(
                'max_angular_speed',
                Parameter.Type.DOUBLE,
                angular
            )
        ])

        response.success = all(r.successful for r in results)

        response.message = (
            'Speed limits updated!'
            if response.success
            else 'Failed to update speed limits!'
        )

        return response

    def goal_callback(self, goal):
        target = goal.target

        values = [target.x, target.y, target.yaw]

        if not all(math.isfinite(v) for v in values):
            return GoalResponse.REJECT

        if not (0.5 <= target.x <= 10.5 and
                0.5 <= target.y <= 10.5):
            return GoalResponse.REJECT

        with self.goal_lock:
            if self.busy:
                return GoalResponse.REJECT
            self.busy = True

        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        return CancelResponse.ACCEPT

    def normalize_angle(self, angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    def stop_turtle(self):
        self.vel_pub.publish(Twist())

    def execute_callback(self, goal_handle):
        target = goal_handle.request.target
        result = GoToPose.Result()
        feedback = GoToPose.Feedback()

        self.get_logger().info(
            f'New goal: x={target.x}, y={target.y}, yaw={target.yaw}'
        )

        try:
            while rclpy.ok():

                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    result.success = False
                    result.message = 'Goal canceled'
                    return result

                pose = self.current_pose

                if pose is None:
                    time.sleep(0.05)
                    continue

                # Position errors
                dx = target.x - pose.x
                dy = target.y - pose.y
                distance = math.hypot(dx, dy)

                # Read live speed limits
                max_linear = self.get_parameter(
                    'max_linear_speed'
                ).value

                max_angular = self.get_parameter(
                    'max_angular_speed'
                ).value

                cmd = Twist()

                if distance > 0.1:

                    desired_angle = math.atan2(dy, dx)

                    angle_error = self.normalize_angle(
                        desired_angle - pose.theta
                    )

                    # Rotate first if necessary
                    if abs(angle_error) > 0.2:
                        cmd.linear.x = 0.0
                    else:
                        cmd.linear.x = min(
                            max_linear, 1.5 * distance
                        )

                    cmd.angular.z = max(
                        -max_angular,
                        min(max_angular, 4.0 * angle_error)
                    )

                else:
                    # Rotate to final requested yaw
                    yaw_error = self.normalize_angle(
                        target.yaw - pose.theta
                    )

                    if abs(yaw_error) < 0.05:
                        self.stop_turtle()
                        goal_handle.succeed()

                        result.success = True
                        result.message = 'Target reached!'

                        self.get_logger().info(
                            'Goal completed successfully!'
                        )
                        return result

                    cmd.angular.z = max(
                        -max_angular,
                        min(max_angular, 4.0 * yaw_error)
                    )

                self.vel_pub.publish(cmd)

                # Action feedback
                feedback.remaining_distance = distance
                feedback.remaining_yaw = self.normalize_angle(
                    target.yaw - pose.theta
                )

                goal_handle.publish_feedback(feedback)

                time.sleep(0.05)

            result.success = False
            result.message = 'ROS shutdown'
            return result

        except Exception as error:
            self.get_logger().error(str(error))
            goal_handle.abort()
            result.success = False
            result.message = str(error)
            return result

        finally:
            self.stop_turtle()

            with self.goal_lock:
                self.busy = False


def main(args=None):
    rclpy.init(args=args)

    node = GoToPoseServer()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
