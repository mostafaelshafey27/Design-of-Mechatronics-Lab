import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from std_srvs.srv import Empty, Trigger
from turtlesim.srv import TeleportAbsolute, SetPen
from geometry_msgs.msg import Twist


class ResetServer(Node):

    def __init__(self):
        super().__init__('reset_server')

        self.group = ReentrantCallbackGroup()

        # Clients for Turtlesim services
        self.clear_client = self.create_client(
            Empty, '/clear',
            callback_group=self.group
        )

        self.teleport_client = self.create_client(
            TeleportAbsolute, '/turtle1/teleport_absolute',
            callback_group=self.group
        )

        self.pen_client = self.create_client(
            SetPen, '/turtle1/set_pen',
            callback_group=self.group
        )

        # Stop turtle movement
        self.vel_pub = self.create_publisher(
            Twist, '/turtle1/cmd_vel', 10
        )

        # Our custom reset service
        self.reset_service = self.create_service(
            Trigger,
            '/reset_turtle',
            self.reset_callback,
            callback_group=self.group
        )

        self.get_logger().info('Reset Server is ready!')

    async def reset_callback(self, request, response):

        self.get_logger().info('Reset requested')

        # Check required services
        clients = [
            self.clear_client,
            self.teleport_client,
            self.pen_client
        ]

        if not all(client.service_is_ready() for client in clients):
            response.success = False
            response.message = 'Turtlesim services are not ready'
            return response

        try:
            # Step 1: Stop the turtle
            self.vel_pub.publish(Twist())

            # Step 2: Disable pen
            pen_off = SetPen.Request()
            pen_off.r = 255
            pen_off.g = 255
            pen_off.b = 255
            pen_off.width = 2
            pen_off.off = 1

            await self.pen_client.call_async(pen_off)

            # Step 3: Teleport to original position
            teleport = TeleportAbsolute.Request()
            teleport.x = 5.544445
            teleport.y = 5.544445
            teleport.theta = 0.0

            await self.teleport_client.call_async(teleport)

            # Step 4: Clear the drawing
            await self.clear_client.call_async(
                Empty.Request()
            )

            # Step 5: Enable pen again
            pen_on = SetPen.Request()
            pen_on.r = 255
            pen_on.g = 255
            pen_on.b = 255
            pen_on.width = 2
            pen_on.off = 0

            await self.pen_client.call_async(pen_on)

            response.success = True
            response.message = 'Turtle reset successfully!'

            self.get_logger().info(
                'Turtle reset completed!'
            )

        except Exception as error:
            response.success = False
            response.message = str(error)
            self.get_logger().error(str(error))

        return response


def main(args=None):
    rclpy.init(args=args)

    node = ResetServer()
    executor = MultiThreadedExecutor(num_threads=2)
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
