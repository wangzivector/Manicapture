#!/usr/bin/env python3
import os
import rospy
import rospy.logger_level_service_caller
from std_msgs.msg import UInt16MultiArray
import yaml
import numpy as np

class JointMappingProc:
    def __init__(self):
        rospy.init_node('joint_map_node')
        rospy.Subscriber('/hardware_joints', UInt16MultiArray, self.callback)
        
        script_dir = os.path.dirname(os.path.realpath(__file__))
        self.cfg_path = script_dir + "/../cfg/jointmap.yaml"

        with open(self.cfg_path, 'r') as file:
            self.jointmap = yaml.safe_load(file)
        rospy.loginfo("current jointmap: {}".format(self.jointmap))

        self.map_fun(self.jointmap)

        with open(self.cfg_path, 'r') as file:
            self.jointmap = yaml.safe_load(file)
        rospy.loginfo("finished jointmap: {}".format(self.jointmap))
        

    def callback(self, msg):
        self.joint_current = np.array(msg.data).astype(np.float32)
        
    def map_fun(self, jointmap):
        # joint_names = ['j11', 'j12', 'j13', 'j14', 'j21', 'j22', 'j23', 'j31', 'j32', 'j33', 'jj1', 'jj2']
        joint_names = jointmap['joint_names']
        # joint_ids = jointmap['joint_ids']
        joint_num = len(joint_names)

        rospy.loginfo("available_joint_names: {}".format(joint_names))
        rospy.loginfo("activate joints one by one with instruction:")
        rospy.logwarn("{}".format(joint_names))

        joints, indices = [], []
        while len(joint_names) > 0:
            print("\n###")
            rospy.loginfo("please quickly rotate joint [{}]. ".format(joint_names[0]))
            input("press [Enter] and roll for 3 seconds:")
            rospy.sleep(2)
            rospy.loginfo("collecting data for joint [{}]".format(joint_names[0]))
            joint_collection = []
            for k in range(30):
                rospy.sleep(0.1)
                joint_collection.append(self.joint_current)

            joint_collection = np.array(joint_collection)
            joint_var = np.std(joint_collection, axis=0)
            rospy.loginfo("joint_var: \n{}".format(joint_var))
            sort_var = np.sort(joint_var, axis=None)
            rospy.loginfo("var ratio:  {}".format(sort_var[-1] / sort_var[-2]))
            if input("acceptable for joint {} as id {} [Enter/n]:".format(joint_names[0], np.argmax(joint_var))) != 'n':
                indices.append(int(np.argmax(joint_var)))
                joints.append(joint_names.pop(0))
                rospy.loginfo("result so far: {}/{}".format(joints, indices))
            else:
                rospy.logwarn("remap for joint [{}]".format(joint_names[0]))

            if len(indices) != len(set(indices)): # elements are unique
                rospy.logerr("id list confusing, please try again: {}".format(indices))
                # return
            
            print("###\n")

        with open(self.cfg_path, 'w', encoding='utf-8') as file:
            yaml.dump({'joint_names': joints, 'joint_ids': indices}, file, default_flow_style=False, allow_unicode=True)



if __name__ == '__main__':
    try:
        JointMappingProc()
    except rospy.ROSInterruptException:
        pass



