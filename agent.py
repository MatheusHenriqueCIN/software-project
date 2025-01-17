from utils.ssl.Navigation import Navigation
from utils.ssl.base_agent import BaseAgent
import math

class ExampleAgent(BaseAgent):
    def __init__(self, id=0, yellow=False):
        super().__init__(id, yellow)

    def decision(self):
        if len(self.targets) == 0:
            return

        obstacles = self.detect_obstacle_in_path()

        if obstacles:
            closest_target = self.get_closest_target()
            target_velocity, target_angle_velocity = self.avoid_obstacles_and_go_to_target(closest_target, obstacles)
        else:
            closest_target = self.get_closest_target()
            target_velocity, target_angle_velocity = Navigation.goToPoint(self.robot, closest_target)

        self.set_vel(target_velocity)
        self.set_angle_vel(target_angle_velocity)

    def post_decision(self):
        pass

    def detect_obstacle_in_path(self):
        detection_range = 3.0
        detection_angle = math.pi / 6

        obstacles = []

        for angle in [0, detection_angle, -detection_angle, detection_angle / 2, -detection_angle / 2]:
            obstacle_x = self.robot.x + detection_range * math.cos(angle)
            obstacle_y = self.robot.y + detection_range * math.sin(angle)

            if self.is_obstacle_in_path(obstacle_x, obstacle_y):
                obstacles.append((obstacle_x, obstacle_y))

        return obstacles

    def is_obstacle_in_path(self, x, y):
        distance = math.sqrt((x - self.robot.x)**2 + (y - self.robot.y)**2)
        return distance < 0.7

    def avoid_obstacles_and_go_to_target(self, target, obstacles):
        target_velocity, target_angle_velocity = Navigation.goToPoint(self.robot, target)

        avoidance_angle = 0
        adjusted_velocity = target_velocity

        for obstacle in obstacles:
            obstacle_x, obstacle_y = obstacle
            angle_to_obstacle = math.atan2(obstacle_y - self.robot.y, obstacle_x - self.robot.x)

            avoidance_angle += 20 if angle_to_obstacle < 0 else -20

            adjusted_velocity *= 0.5

        target_angle_velocity += avoidance_angle

        return adjusted_velocity, target_angle_velocity

    def get_closest_target(self):
        closest_target = min(self.targets, key=lambda target: self.distance_to(self.robot, target))
        return closest_target

    def distance_to(self, robot, target):
        robot_x, robot_y = robot.x, robot.y
        target_x, target_y = target.x, target.y
        distance = math.sqrt((target_x - robot_x)**2 + (target_y - robot_y)**2)
        return distance
