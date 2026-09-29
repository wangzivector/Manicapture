#!/usr/bin/env python3
import rospy
import tf
import numpy as np
from collections import deque
from geometry_msgs.msg import PoseWithCovarianceStamped
from tf.transformations import euler_from_quaternion, quaternion_from_euler

# ------------------------------
# Helpers
# ------------------------------
def angle_wrap(x):
    return (x + np.pi) % (2 * np.pi) - np.pi

def apply_angle_wrap(vec, angle_indices):
    if not angle_indices:
        return vec
    vec = vec.copy()
    for idx in angle_indices:
        vec[idx] = angle_wrap(vec[idx])
    return vec

class WeightedMovingAverage:
    def __init__(self, weights):
        self.weights = np.array(weights, dtype=float)
        self.weights /= np.sum(self.weights)
        self.buffer = deque(maxlen=len(weights))

    def filter(self, new_val):
        self.buffer.append(np.array(new_val).reshape(-1, 1))
        if len(self.buffer) < len(self.weights):
            return self.buffer[-1]
        return sum(self.weights[i] * self.buffer[-(i+1)]
                   for i in range(len(self.weights)))

class EKF:
    def __init__(self, x0, P0):
        self.x = np.atleast_2d(x0).astype(float)
        if self.x.shape[0] < self.x.shape[1]:
            self.x = self.x.T
        self.P = np.array(P0, dtype=float)

    def predict(self, F, Q):
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q

    def update(self, z, H, R, gating="mahalanobis", threshold=None, angle_indices=None):
        z = np.atleast_2d(z)
        if z.shape[0] < z.shape[1]:
            z = z.T
        z_pred = H @ self.x
        y = apply_angle_wrap(z - z_pred, angle_indices)
        S = H @ self.P @ H.T + R
        accept = True
        if threshold is not None:
            if gating == "euclidean":
                accept = float(np.linalg.norm(y)) < threshold
            elif gating == "mahalanobis":
                try:
                    Sinv_y = np.linalg.solve(S, y)
                except np.linalg.LinAlgError:
                    Sinv_y = np.linalg.pinv(S) @ y
                accept = float((y.T @ Sinv_y).squeeze()) < threshold
        if accept:
            try:
                K = self.P @ H.T @ np.linalg.inv(S)
            except np.linalg.LinAlgError:
                K = self.P @ H.T @ np.linalg.pinv(S)
            self.x = self.x + K @ y
            I = np.eye(self.P.shape[0])
            self.P = (I - K @ H) @ self.P
        return accept

# ------------------------------
# ROS Node
# ------------------------------
class PoseEKFNode:
    def __init__(self):
        rospy.init_node('manipose_flt_node')
        self.listener = tf.TransformListener()
        self.br = tf.TransformBroadcaster()

        self.parent_frame = rospy.get_param('~parent_frame')
        self.child_frame = rospy.get_param('~child_frame')
        self.child_frame_filtered = self.child_frame + "_flt"
        
        self.pub = rospy.Publisher(self.child_frame+"_flt", PoseWithCovarianceStamped, queue_size=10)

        x0 = np.zeros((6, 1))
        P0 = np.eye(6) * 0.1
        self.ekf = EKF(x0, P0)

        self.Q = np.diag([0.01]*6)
        self.R = np.diag([0.05, 0.05, 0.05, 0.1, 0.1, 0.1])
        self.angle_indices = [3, 4, 5]
        self.H = np.eye(6)
        self.threshold = 10.0

        # weights = rospy.get_param('~pos_filter_weights', [0.5, 0.3, 0.2])
        # weights = [1.0]
        weights = [0.4, 0.3, 0.2, 0.1]
        self.pos_filter = WeightedMovingAverage(weights)

    def run(self):
        rate = rospy.Rate(300)
        last_time = None
        while not rospy.is_shutdown():
            try:
                # self.listener.waitForTransform(self.child_frame, self.parent_frame, rospy.Time.now(), rospy.Duration(100))
                time = self.listener.getLatestCommonTime(self.parent_frame, self.child_frame)
                if last_time == time:
                    rate.sleep()
                    continue
                else:
                    last_time = time
                
                (trans, rot) = self.listener.lookupTransform(self.parent_frame, self.child_frame, time)
                roll, pitch, yaw = euler_from_quaternion(rot)
                pos = self.pos_filter.filter([[trans[0]], [trans[1]], [trans[2]]])
                z = np.vstack((pos, [[roll], [pitch], [yaw]]))
                F = np.eye(6)
                self.ekf.predict(F, self.Q)
                accepted = self.ekf.update(z, self.H, self.R,
                                           gating="mahalanobis",
                                           threshold=self.threshold,
                                           angle_indices=self.angle_indices)
                if accepted:
                    self.publish_pose_and_tf()

            except (tf.Exception, tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
                pass
            # self.rate.sleep()

    def publish_pose_and_tf(self):
        # --- Publish PoseWithCovarianceStamped ---
        msg = PoseWithCovarianceStamped()
        msg.header.stamp = rospy.Time.now()
        msg.header.frame_id = self.parent_frame
        x, y, z, roll, pitch, yaw = self.ekf.x.flatten()
        quat = quaternion_from_euler(roll, pitch, yaw)
        msg.pose.pose.position.x = x
        msg.pose.pose.position.y = y
        msg.pose.pose.position.z = z
        msg.pose.pose.orientation.x = quat[0]
        msg.pose.pose.orientation.y = quat[1]
        msg.pose.pose.orientation.z = quat[2]
        msg.pose.pose.orientation.w = quat[3]
        cov = self.ekf.P.flatten().tolist()
        msg.pose.covariance = cov + [0.0]*(36 - len(cov))
        self.pub.publish(msg)

        # --- Broadcast TF ---
        self.br.sendTransform(
            (x, y, z),
            quat,
            rospy.Time.now(),
            self.child_frame_filtered,
            self.parent_frame
        )

# ------------------------------
if __name__ == '__main__':
    try:
        node = PoseEKFNode()
        node.run()
    except rospy.ROSInterruptException:
        pass
