# ROS 2 Turtlesim Control System

**Design of Mechatronics Systems — Lab 1 Assignment**

Alexandria University — Faculty of Engineering

## 1. Team Members

| Name | Student ID |
|---|---|
| Mostafa Moataz | 9756 |
| Abdullah Mohamed | 9757 |
| Amr Khalid | 9765 |

## 2. Project Overview

This project implements a ROS 2 control system using the Turtlesim simulator.

The system can move a turtle to a target position and orientation, control its maximum movement speeds, reset the simulator, and automatically draw a square using ROS 2 Actions and Services.

The project is developed using **ROS 2 Humble, Ubuntu 22.04, and Python**.

## 3. ROS 2 Packages

### turtle_interfaces

This package contains the custom ROS 2 interfaces:

- `TargetPose.msg` — Defines the target x, y, and yaw.
- `GoToPose.action` — Defines the movement goal, result, and feedback.
- `DrawSquare.action` — Defines the square side length, result, and progress.
- `SetSpeedLimits.srv` — Defines the request and response for changing speed limits.

### turtle_controller

This package contains the control nodes:

- `go_to_pose_server.py` — Moves the turtle to the required position and orientation.
- `reset_server.py` — Clears the simulator and returns the turtle to its original position.
- `square_server.py` — Draws a square using four GoToPose action goals.
- `system.launch.py` — Starts the complete system.

## 4. Requirements

- Ubuntu 22.04
- ROS 2 Humble
- Python 3
- Turtlesim
- Colcon

Install the required packages:

```bash
sudo apt update
sudo apt install ros-humble-turtlesim python3-colcon-common-extensions
```

## 5. Build Instructions

Create a new ROS 2 workspace:

```bash
source /opt/ros/humble/setup.bash
mkdir -p ~/ros2_lab_ws/src
cd ~/ros2_lab_ws/src
```

Clone this repository into the `src` directory:

```bash
git clone https://github.com/mostafaelshafey27/Design-of-Mechatronics-Lab.git .
```

The directory should be empty before cloning into it using `.`.

Build the packages:

```bash
cd ~/ros2_lab_ws
colcon build --symlink-install
source install/setup.bash
```

## 6. Run the Complete System

Start all ROS 2 nodes using one launch command:

```bash
ros2 launch turtle_controller system.launch.py
```

This launches Turtlesim, the GoToPose Action Server, the Reset Service, and the Square Action Server.

Default speed parameters:

- Maximum linear speed: 1.5
- Maximum angular speed: 1.5

For the following tests, open a new terminal and run:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_lab_ws/install/setup.bash
```

Keep the launch terminal running.

## 7. Testing

### 7.1 Verify the nodes

```bash
ros2 node list
```

Expected nodes include:

- `/turtlesim`
- `/go_to_pose_server`
- `/reset_server`
- `/square_server`

### 7.2 Verify custom interfaces

```bash
ros2 interface show turtle_interfaces/msg/TargetPose
ros2 interface show turtle_interfaces/action/GoToPose
ros2 interface show turtle_interfaces/action/DrawSquare
ros2 interface show turtle_interfaces/srv/SetSpeedLimits
```

### 7.3 Move the turtle to a target pose

```bash
ros2 action send_goal /go_to_pose turtle_interfaces/action/GoToPose "{target: {x: 8.0, y: 7.0, yaw: 1.57}}" --feedback
```

Check the turtle's final position:

```bash
ros2 topic echo /turtle1/pose --once
```

The controller uses position and orientation tolerances to determine when the goal is reached.

### 7.4 Change speed limits

Check the current parameters:

```bash
ros2 param get /go_to_pose_server max_linear_speed
ros2 param get /go_to_pose_server max_angular_speed
```

Update the maximum speeds:

```bash
ros2 service call /set_speed_limits turtle_interfaces/srv/SetSpeedLimits "{max_linear_speed: 1.0, max_angular_speed: 2.0}"
```

Test invalid speeds:

```bash
ros2 service call /set_speed_limits turtle_interfaces/srv/SetSpeedLimits "{max_linear_speed: -1.0, max_angular_speed: 0.0}"
```

Invalid speed values should be rejected.

The speed limits can also be changed while the turtle is moving.

### 7.5 Reset the turtle

```bash
ros2 service call /reset_turtle std_srvs/srv/Trigger "{}"
```

The reset service clears the drawing and returns the turtle to approximately:

- X = 5.544445
- Y = 5.544445
- Yaw = 0.0

### 7.6 Draw a square

```bash
ros2 action send_goal /draw_square turtle_interfaces/action/DrawSquare "{side_length: 3.0}" --feedback
```

The Square Action Server resets the simulator and executes four sequential GoToPose goals.

Expected feedback:

```text
sides_completed: 1
sides_completed: 2
sides_completed: 3
sides_completed: 4
```

The action returns a successful result after completing the square.

Run the same command again to verify that the old drawing is cleared before a new square is drawn.

## 8. Test Results

The following functionality has been tested:

- Custom interface generation and successful package builds.
- GoToPose movement to different target positions.
- Action feedback and successful results.
- Position and orientation accuracy within the selected tolerances.
- Speed parameter updates using ROS 2 Services.
- Rejection of invalid speed values.
- Reset service operation and position verification.
- Square drawing with four sequential movement goals.
- Launching the integrated system using a ROS 2 launch file.

## 9. Conclusion

The project demonstrates the integration of ROS 2 Nodes, Topics, Messages, Services, Actions, Parameters, and Launch Files.

The resulting system provides automatic turtle movement, runtime speed configuration, simulator resetting, and square drawing through reusable ROS 2 components.
