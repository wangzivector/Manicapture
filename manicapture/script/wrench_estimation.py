#! /usr/bin/env python3

import time
import rospy
import numpy as np
np.set_printoptions(precision=3)
import onnxruntime as ort
from geometry_msgs.msg import TwistStamped
from std_msgs.msg import Float32MultiArray
import sys
# from scipy.ndimage import gaussian_filter

class OptTacWrenchEst:
    def __init__(self) -> None:
        rub_type = "e10"
        data_path = "/home/smart/catkin_ws/src/phototactile/data"
        self.session_fr = ort.InferenceSession(f"{data_path}/model_{rub_type}_forces.onnx")
        self.session_tr = ort.InferenceSession(f"{data_path}/model_{rub_type}_torque.onnx")
        self.input_name_fr = self.session_fr.get_inputs()[0].name
        self.input_name_tr = self.session_tr.get_inputs()[0].name
        self.est_poses = []
        self.est_wrench = []
        self.pub_wren_ids = []
        self.set_zero_ref = False
        self.ref_flag = False

        self.ref_mean_bank_size = 10
        self.ref_bank = []

        rospy.logwarn(f"wrench regression model is {rub_type}")
        rospy.Subscriber('tt_distactile', Float32MultiArray, self.pointarray_cb)
        self.pub_wrens = rospy.Publisher('est_wrench', Float32MultiArray, queue_size=1)
        #TODO wrap follow to WrenchStamped msg
        rospy.sleep(0.2)

    def set_zero_effset(self, ref_size = 15):
        self.ref_mean_bank_size = ref_size
        self.set_zero_ref = True
        self.ref_flag = False
        self.ref_bank = []
        rospy.loginfo("optictac flag set sensor zeros.")

    def pointarray_cb(self, msg):
        TACID = msg.layout.data_offset

        if TACID == len(self.est_poses):
            self.est_poses.append(None)
            self.est_wrench.append(None)
            self.pub_wren_ids.append(rospy.Publisher(f'est_wrench_{TACID}', Float32MultiArray, queue_size=1))
            self.set_zero_effset()
        if TACID > len(self.est_poses): return

        if len(msg.data) == 384:
            d_point = np.array(msg.data).reshape(64, 6)
            self.est_poses[TACID] = d_point.reshape((8, 8, 6))
            pgrids = d_point[:, 3:].reshape((1, 8, 8, 3))
        elif len(msg.data) == 216:
            d_point = np.array(msg.data).reshape(36, 6)
            self.est_poses[TACID] = d_point.reshape((6, 6, 6))
            pgrids = np.zeros((1, 8, 8, 3))
            pgrids[0, 1:-1, 1:-1] = d_point[:, 3:].reshape((6, 6, 3))
            pgrids[0, 0] = pgrids[0, 1]
            pgrids[0, -1] = pgrids[0, -2]
            pgrids[0, :, 0] = pgrids[0, :, 1]
            pgrids[0, :, -1] = pgrids[0, :, -2]
        else: raise ValueError(f"Wrong msg format for unpack: len {len(msg.data)}")

        input_x = pgrids.transpose((0, 3, 1, 2)).astype(np.float32)*1000
        input_x_for_depth = input_x.copy()
        self.est_wrench[TACID] = np.array(
            self.session_fr.run(None, {self.input_name_fr: input_x})[0].squeeze().tolist() + 
            [self.session_tr.run(None, {self.input_name_tr: input_x})[0].squeeze().tolist()] # /100
        )
        self.est_wrench[TACID][2] = self.session_fr.run(None, {self.input_name_fr: input_x_for_depth})[0].squeeze()[2]

        for est in self.est_wrench: 
            if est is None: return
        if not self.set_zero_ref: return
        if not self.ref_flag: 
            self.ref_bank.append(self.est_wrench.copy())
            if len(self.ref_bank) >= self.ref_mean_bank_size:
                self.ref_pt_wrench = np.mean(self.ref_bank, axis=0)
                self.ref_flag = True
            else: 
                self.est_wrench = [None] * len(self.ref_bank[0])
                return

        est_wrench_net = self.est_wrench[TACID] - self.ref_pt_wrench[TACID]
        self.pub_wren_ids[TACID].publish(Float32MultiArray(data=est_wrench_net.tolist()))
        data_wren = Float32MultiArray(data=est_wrench_net.tolist())
        data_wren.layout.data_offset = TACID
        self.pub_wrens.publish(data_wren)
        rospy.loginfo(f"{[TACID]} Wrench: {est_wrench_net}")



if __name__ == '__main__':
    rospy.init_node('wrench_estimation_node')
    optictac = OptTacWrenchEst()
    optictac.set_zero_effset()
    
    rosrate = rospy.Rate(10)
    while not rospy.is_shutdown():
        if rospy.is_shutdown(): exit()
        try:
            if input("Set zero offset to sensors?") == 'q': exit()
            optictac.set_zero_effset()
        except KeyboardInterrupt:
            print("\nExiting by user with Ctrl+C.")
            sys.exit(0)
