
import math
import threading

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from std_srvs.srv import Trigger
from turtle_interfaces.action import GoToPose, DrawSquare


class SquareServer(Node):

    def __init__(self):
        super().__init__('square_server')

        self.group = ReentrantCallbackGroup()
        self.goal_lock = threading.Lock()
        self.busy = False

        # Client for our Reset Service
        self.reset_client = self.create_client(
            Trigger,
            '/reset_turtle',
            callback_group=self.group
        )

        # Client for our GoToPose Action
        self.goto_client = ActionClient(
            self,
            GoToPose,
            '/go_to_pose',
            callback_group=self.group
        )

        # Square Action Server
        self.square_server = ActionServer(
            self,
            DrawSquare,
            '/draw_square',
            execute_callback=self.execute_square,
            goal_callback=self.goal_callback,
            callback_group=self.group
        )

        self.get_logger().info(
            'Square Action Server is ready!'
        )

    def goal_callback(self, request):

        side = request.side_length

        # Keep the square inside Turtlesim
        if not math.isfinite(side) or not (0.2 <= side <= 4.0):
            return GoalResponse.REJECT

        with self.goal_lock:
            if self.busy:
                return GoalResponse.REJECT

            self.busy = True

        return GoalResponse.ACCEPT

    async def execute_square(self, goal_handle):

        result = DrawSquare.Result()
        side = goal_handle.request.side_length

        try:
            # Check required servers
            if not self.reset_client.wait_for_service(
                timeout_sec=5.0
            ):
                raise RuntimeError('Reset service not available')

            if not self.goto_client.wait_for_server(
                timeout_sec=5.0
            ):
                raise RuntimeError('GoToPose server not available')

            # Step 1: Reset turtle
            self.get_logger().info('Resetting turtle...')

            reset_response = await self.reset_client.call_async(
                Trigger.Request()
            )

            if not reset_response.success:
                raise RuntimeError(reset_response.message)

            # Starting position
            start_x = 5.544445
            start_y = 5.544445

            # Four corners = four GoToPose goals
            corners = [
                (start_x + side, start_y, 0.0),
                (start_x + side, start_y + side, math.pi / 2),
                (start_x, start_y + side, math.pi),
                (start_x, start_y, -math.pi / 2)
            ]

            for i, (x, y, yaw) in enumerate(corners, start=1):

                self.get_logger().info(
                    f'Moving to corner {i}'
                )

                # Create GoToPose goal
                goal = GoToPose.Goal()
                goal.target.x = float(x)
                goal.target.y = float(y)
                goal.target.yaw = float(yaw)

                # Send goal and wait for acceptance
                turtle_goal = await self.goto_client.send_goal_async(
                    goal
                )

                if not turtle_goal.accepted:
                    raise RuntimeError(
                        f'Corner {i} goal rejected'
                    )

                # Wait until turtle reaches the corner
                response = await turtle_goal.get_result_async()

                if not response.result.success:
                    raise RuntimeError(
                        f'Corner {i} failed: {response.result.message}'
                    )

                # Send Square feedback
                feedback = DrawSquare.Feedback()
                feedback.sides_completed = i

                goal_handle.publish_feedback(feedback)

                self.get_logger().info(
                    f'Side {i} completed!'
                )

            # Square completed
            goal_handle.succeed()

            result.success = True
            result.message = 'Square completed successfully!'

            self.get_logger().info(
                'Square completed successfully!'
            )

            return result

        except Exception as error:

            self.get_logger().error(str(error))
            goal_handle.abort()

            result.success = False
            result.message = str(error)

            return result

        finally:
            with self.goal_lock:
                self.busy = False


def main(args=None):

    rclpy.init(args=args)

    node = SquareServer()

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
