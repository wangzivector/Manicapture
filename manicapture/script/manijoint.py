#!/usr/bin/env python3
import os
import rospy
from std_msgs.msg import UInt16MultiArray
from sensor_msgs.msg import JointState
import yaml


class JointStatePublisher:
    def __init__(self):
        rospy.init_node('motion_joint_node')

        self.joint_pub = rospy.Publisher('/joint_states', JointState, queue_size=10)
        rospy.Subscriber('/hardware_joints', UInt16MultiArray, self.callback)
        
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.cfg_path = script_dir + "/../cfg/jointmap.yaml"

        with open(self.cfg_path, 'r') as file:
            self.jointmap = yaml.safe_load(file)
        rospy.spin()

    def callback(self, msg):
        joint_state = JointState()
        joint_state.header.stamp = rospy.Time.now()
        joint_state.name = self.jointmap['joint_names']
        # msg.data is the angles*100 (in degree) with 180 degree offset, convert to radius 333.3
        joint_angs = [(((float(dt)/(2**15)) - 0.5) * 320 / 180 * 3.14159265) for dt in msg.data]
        joint_state.position = [joint_angs[id] for id in self.jointmap['joint_ids']]
        self.joint_pub.publish(joint_state)

if __name__ == '__main__':
    try:
        JointStatePublisher()
    except rospy.ROSInterruptException:
        pass

