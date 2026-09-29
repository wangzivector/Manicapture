#!/usr/bin/env python3
import rospy
import numpy as np
import time
import pickle
from std_msgs.msg import UInt16MultiArray, Float32MultiArray, MultiArrayDimension
from geometry_msgs.msg import WrenchStamped

np.set_printoptions(precision=4, suppress=True)


class ManiTactile:
    def __init__(self):
        self.last_time = [time.time() for i in range(4)]
        self.pt_cst = [[], [], [], []]
        self.pt_opgs = [None, None, None, None]
        self.last_opgs = [None, None, None, None]
        self.pt_sense = [None, None, None, None]

        rospy.Subscriber('hardware_photos', UInt16MultiArray, self.photo_callback)
        self.pub_distactile = rospy.Publisher('tt_distactile', Float32MultiArray, queue_size=4)
        self.pub_photodigit = rospy.Publisher('tt_photodigit', Float32MultiArray, queue_size=4)
        # self.pub_contact = rospy.Publisher('tt_contact', WrenchStamped, queue_size=4)

        self.initial_batchsize = 10
        self.initial_data_var = 2e-4
        self.method_set = {"gaussian": self.gaussian_opti, 'intensity': self.intensity_opt}
        self.opt_mehod = rospy.get_param("~photo_optimization", default="gaussian")
        self.optifun = self.method_set[self.opt_mehod]

    def photo_callback(self, data):
        ## data extraction
        HEADERSIZE = data.data[0]
        if HEADERSIZE == 0: 
            rospy.logwarn("Wrong msg with Headsize == 0, disgard msg")
            return
        TACTSIZE, TACTID, GRIDLENGTH, PADSIZE, ADCRES, SENSEDELAY, SPACING, UDRANGE, SEQUENCE = data.data[1:HEADERSIZE]
        ptdata = np.array(data.data[HEADERSIZE:])
        self.GRIDPHOTO = ptdata[:GRIDLENGTH]
        self.PADPHOTOX = ptdata[GRIDLENGTH:(GRIDLENGTH+PADSIZE)] - 4 # (1, 7) to (-3, -3)
        self.PADPHOTOY = ptdata[(GRIDLENGTH+PADSIZE):(GRIDLENGTH+PADSIZE*2)] - 4 # (1, 7) to (-3, -3)
        # self.PADEDGE = np.max(np.max(np.abs([self.PADPHOTOX, self.PADPHOTOY])))
        ptencode = ptdata[(GRIDLENGTH+PADSIZE*2):(GRIDLENGTH+PADSIZE*2+GRIDLENGTH**2)] # GRIDLENGTH * GRIDLENGTH
        ptread = ptdata[(GRIDLENGTH+PADSIZE*2+GRIDLENGTH**2):].astype(np.float32) # (GRIDLENGTH, GRIDLENGTH, PADSIZE)
        self.update_photo(TACTID, ptencode, ptread, GRIDLENGTH, PADSIZE)

        ## preprocessing
        photodigits_c = self.pt_sense[TACTID] / (np.power(2, ADCRES) - 1) # (GRIDLENGTH, GRIDLENGTH, PADSIZE)
        self.initialize_photo(TACTID, photodigits_c, GRIDLENGTH, refresh = (SEQUENCE == 0))
        if not isinstance(self.pt_cst[TACTID], np.ndarray): return False # no averaged initialization yet

        ## tactile x-y-h optimization
        start_opt_time = time.time()
        POINTSIZE, PADS = GRIDLENGTH*GRIDLENGTH, [self.PADPHOTOX, self.PADPHOTOY]
        iterations, retSSE, optgs = self.optifun(photodigits_c, self.last_opgs[TACTID], POINTSIZE, PADS)
        self.last_opgs[TACTID] = optgs.copy()
        # print('np.var(optgs[:, 0])', np.var(optgs[:, 0]))
        if np.var(optgs[:, 0]) < 0.003 and self.opt_mehod == 'intensity': 
            rospy.logwarn(f"updating he with var {np.var(optgs[:, 0])}")
            self.pt_opgs[TACTID] = self.pt_opgs[TACTID] + 0.1 * (optgs.copy() - self.pt_opgs[TACTID])
        ## decompose active force
        distactile = self.compute_tactile(self.pt_opgs[TACTID], optgs, SPACING, self.GRIDPHOTO)
        
        ## advertise_photodigits
        self.advertise_photodigits(TACTID, photodigits_c)
        
        ## (interpolated) deformation advertisement
        self.advertise_distactile(TACTID, distactile)

        # ## advertise contact forces
        # self.advertise_contact(TACTID, wrench_pred)

        ## logging
        # time_opti = time.time() - start_opt_time
        # rospy.logwarn(time_opti*1000) # several ms
        update_period = time.time() - self.last_time[TACTID]
        self.last_time[TACTID] = time.time()
        # rospy.loginfo("ID:{} iter:{} sse:{:.03f} var:{} time:{:.03f}ms".format( TACTID, iterations, retSSE.mean(), optgs.shape, (time_opti)*1000))
        rospy.loginfo("ID:{}/{} {:.01f}Hz/{:.01f}ms DL:{}us RES:{} GD:{} PAD:{} PT:{}".format(
            TACTID, TACTSIZE, 1/update_period, update_period*1000, SENSEDELAY, ADCRES, 
            self.GRIDPHOTO.shape, self.PADPHOTOX.shape, photodigits_c.shape))

    def advertise_distactile(self, TACTID, distactile):
        dp_msg = Float32MultiArray()
        dp_msg.layout.data_offset = TACTID
        dp_msg.layout.dim = []
        for dd, dim in enumerate(distactile.shape):
            dp_msg.layout.dim.append(MultiArrayDimension('dim{}'.format(dd), dim, 0))
        dp_msg.data = distactile.flatten().tolist()
        self.pub_distactile.publish(dp_msg)

    def advertise_contact(self, TACTID, wrench):
        wrench_pred = WrenchStamped()
        wrench_pred.header.stamp = rospy.Time.now()
        wrench_pred.header.frame_id = "p{}".format(TACTID+1)
        wrench_pred.wrench.force.x = wrench[0]
        wrench_pred.wrench.force.y = wrench[1]
        wrench_pred.wrench.force.z = wrench[2]
        self.pub_contact.publish(wrench_pred)

    def advertise_photodigits(self, TACTID, photodigits_c):
        if TACTID != rospy.get_param_cached('/machine_server/showrosimage', -1): return
        if not isinstance(self.pt_cst[TACTID], np.ndarray): return

        dg_msg = Float32MultiArray()
        dg_msg.layout.dim = []
        for dd, dim in enumerate(photodigits_c.shape):
            dg_msg.layout.dim.append(MultiArrayDimension('dim{}'.format(dd), dim, 0))
        dg_msg.layout.data_offset = TACTID
        dg_msg.data = photodigits_c.flatten().tolist() + self.pt_cst[TACTID].flatten().tolist()
        self.pub_photodigit.publish(dg_msg)

    def update_photo(self, TACTID, ptencode, ptread, GRIDLENGTH, PADSIZE):
        ptencode_matrix = np.array([[bool(int(digit)) for digit in format(num, '0{}b'.format(PADSIZE))] for num in ptencode])
        ptencode_matrix = np.reshape(np.flip(ptencode_matrix, axis=-1), (GRIDLENGTH, GRIDLENGTH, -1))

        # self.pt_sense (GRIDLENGTH, GRIDLENGTH, PADSIZE)
        if (self.pt_sense[TACTID] is None) or (self.pt_sense[TACTID].shape != ptencode_matrix.shape): 
            self.pt_sense[TACTID] = np.zeros((GRIDLENGTH, GRIDLENGTH, PADSIZE))

        if np.any(ptencode_matrix):
            if ptencode_matrix.sum() == len(ptread):
                self.pt_sense[TACTID][ptencode_matrix] = ptread
            else: rospy.logwarn("The receive photos and positions not match, ignored.")

    def initialize_photo(self, TACTID, photodigits, GRIDLENGTH, refresh):
        if isinstance(self.pt_cst[TACTID], np.ndarray):
            if refresh == True: self.pt_cst[TACTID] = [photodigits]; return False
            if photodigits.shape == self.pt_cst[TACTID].shape:
                return True
            else: self.pt_cst[TACTID] = [photodigits]; return False
        else:
            if len(self.pt_cst[TACTID]) == 0: 
                self.pt_cst[TACTID].append(photodigits); return False
            if photodigits.shape == self.pt_cst[TACTID][-1].shape:
                self.pt_cst[TACTID].append(photodigits)
                if len(self.pt_cst[TACTID]) == self.initial_batchsize:
                    var_buff = np.var(self.pt_cst[TACTID], axis=0).max()
                    if var_buff > self.initial_data_var:
                        rospy.loginfo("[initialize]: data buff high variance: {}, retry ...".format(var_buff)) 
                        self.pt_cst[TACTID] = [photodigits]
                        return False
                    self.pt_cst[TACTID] = np.mean(self.pt_cst[TACTID], axis=0)
                    POINTSIZE, PADS = GRIDLENGTH*GRIDLENGTH, [self.PADPHOTOX, self.PADPHOTOY]
                    _, _, opted = self.optifun(self.pt_cst[TACTID], None, POINTSIZE, PADS, initial=True)
                    self.last_opgs[TACTID] = opted
                    print("initial", opted)
                    self.pt_opgs[TACTID] = opted.copy()
                    return True
                else: return False
            else: self.pt_cst[TACTID] = [photodigits]; return False

    @staticmethod
    def intensity_opt(i_data, init_v, POINTSIZE, PADS, MAX_ITERATION=200, TThreshold=1e-4, initial=False):
        ## reshape to (64 x 9)
        PADSIZE = len(PADS[0])
        dXX = np.tile(np.array(PADS[0]).astype(float), (POINTSIZE, 1)) # (1, 9) -> (64, 9)
        dYY = np.tile(np.array(PADS[1]).astype(float), (POINTSIZE, 1)) # (1, 9) -> (64, 9)
        if i_data.shape != (POINTSIZE, PADSIZE): 
            i_data = np.reshape(i_data, (POINTSIZE, PADSIZE))

        if initial: # fix he, dex, dey; opti i0
            i0 = np.ones((i_data.shape[0], 1)) * 0.25 # (64, 1)
            he = np.ones((i_data.shape[0], 1)) * 0.67 # note: length is 1 unit per cell margin
            dex = np.zeros((i_data.shape[0], 1))
            dey = np.zeros((i_data.shape[0], 1))
            print("Intialized", np.hstack([he, dex, dey, i0]))
        else:
            i0 = init_v[:, 3, np.newaxis]
            he = -init_v[:, 0, np.newaxis]
            dex = init_v[:, 1, np.newaxis]
            dey = init_v[:, 2, np.newaxis]

        ## Parameter Optimization
        last_SSE = None
        iterations = 0
        for iter in range(MAX_ITERATION):
            bias_xx = dXX - dex # (64, 9)
            bias_yy = dYY - dey # (64, 9)
            de_sqt = bias_xx**2 + bias_yy**2
            denominator = (he**2 + de_sqt)**1.5 # (64, 9)
            predict_i = (i0 * he) / denominator # (64, 9)
            error = i_data - predict_i # (64, 9)
            o_SSE = (error * error).sum(axis = 1, keepdims=True) # (64, 9) -> (64, 1)

            ## Gradients for variables
            grad_i0 = 2 * error * (he / denominator)
            gd_denominator = (he**2) + (de_sqt**2.5)
            grad_dex = 2 * error * (3 * i0 * he * bias_xx) / gd_denominator
            grad_dey = 2 * error * (3 * i0 * he * bias_yy) / gd_denominator
            grad_he = 2 * error * (i0 * ((he**2 + de_sqt)**1.5) - (3 * i0 * (he**2) * ((he**2 + de_sqt)**0.5))) / (((he**2) + de_sqt)**3)

            learning_rate = 0.02 # (64, 1)
            if initial:
                i0 += learning_rate * grad_i0.mean(axis=1, keepdims=True) # (64, 9) -> (64,1)
                he += learning_rate * grad_he.sum(axis=1, keepdims=True) # (64, 9) -> (64,1)
                dex += learning_rate * grad_dex.sum(axis=1, keepdims=True) # (64, 9) -> (64,1)
                dey += learning_rate * grad_dey.sum(axis=1, keepdims=True) # (64, 9) -> (64,1)
            else:
                he += learning_rate * grad_he.sum(axis=1, keepdims=True) # (64, 9) -> (64,1)
                dex += learning_rate * grad_dex.sum(axis=1, keepdims=True) # (64, 9) -> (64,1)
                dey += learning_rate * grad_dey.sum(axis=1, keepdims=True) # (64, 9) -> (64,1)
            iterations += 1
            if last_SSE is not None:
                if np.all(np.abs(last_SSE - o_SSE) < TThreshold): break
            print("loss log", iter, o_SSE.mean())
            last_SSE = o_SSE
        return iterations, o_SSE, np.hstack([-he, dex, dey, i0])

    @staticmethod
    def gaussian_opti(datamat, init_v, POINTSIZE, PADS, MAX_ITERATION=200, TThreshold=1e-4, initial=False):
        ## reshape to (64 x 9)
        PADSIZE = len(PADS[0])
        XX = np.tile(np.array(PADS[0]).astype(float), (POINTSIZE, 1)) # (1, 9) -> (64, 9)
        YY = np.tile(np.array(PADS[1]).astype(float), (POINTSIZE, 1)) # (1, 9) -> (64, 9)
        if datamat.shape != (POINTSIZE, PADSIZE): 
            datamat = np.reshape(datamat, (POINTSIZE, PADSIZE))
        
        ## Initialization for [A, x0, y0, sigma_x, sigma_y]
        # init_v = None # for gaussian mode
        vA = datamat.max(axis=1, keepdims=True) # (64, 1)
        vx0 = (XX * datamat).sum(axis=1, keepdims=True) / datamat.sum(axis=1, keepdims=True) # emprical
        vy0 = (YY * datamat).sum(axis=1, keepdims=True) / datamat.sum(axis=1, keepdims=True) # emprical
        vsigma_x = np.ones((datamat.shape[0], 1)) * 0.1 * PADSIZE # (64, 1)
        vsigma_y = np.ones((datamat.shape[0], 1)) * 0.1 * PADSIZE # (64, 1)
        if init_v is not None:
            vA0 = init_v[:, -1, np.newaxis]
            vAs = vA
            vA = vA0 + (vAs - vA0 - (vAs - vA0).mean())
        else:
            vA0 = vA.copy()

        ## Parameter Optimization
        last_SSE = None
        iterations = 0
        for iter in range(MAX_ITERATION):
            bias_xx = XX - vx0 # (64, 9)
            bias_yy = YY - vy0 # (64, 9)
            sq_vsigma_x = vsigma_x * vsigma_x # (64, 1)
            sq_vsigma_y = vsigma_y * vsigma_y # (64, 1)
            predict_Z = vA * np.exp(
                -(bias_xx * bias_xx) / (2 * sq_vsigma_x) 
                -(bias_yy * bias_yy) / (2 * sq_vsigma_y)
                ) # (64, 9)
            error = datamat - predict_Z # (64, 9)
            o_SSE = (error * error).sum(axis = 1, keepdims=True) # (64, 9) -> (64, 1)
            
            ## Gradients for variables
            dA = (2 * error * predict_Z / vA) # (64, 9)
            dx0 = (2 * error * bias_xx / sq_vsigma_x) # (64, 9)
            dy0 = (2 * error * bias_yy / sq_vsigma_y) # (64, 9)
            dsigma_x = (2 * error * (bias_xx * bias_xx) / (sq_vsigma_x * vsigma_x)) # (64, 9)
            dsigma_y = 2 * error * (bias_yy * bias_yy) / (sq_vsigma_y * vsigma_y) # (64, 9)
        
            learning_rate = 0.03 # (64, 1)

            # vA += learning_rate * dA.sum(axis=1, keepdims=True) # (64, 9) -> (64,1)
            vx0 += learning_rate * dx0.sum(axis=1, keepdims=True) # (64, 9) -> (64,1)
            vy0 += learning_rate * dy0.sum(axis=1, keepdims=True) # (64, 9) -> (64,1)
            vsigma_x += learning_rate * dsigma_x.sum(axis=1, keepdims=True) # (64, 9) -> (64,1)
            vsigma_y += learning_rate * dsigma_y.sum(axis=1, keepdims=True) # (64, 9) -> (64,1)
            iterations += 1
            if last_SSE is not None:
                if np.all(np.abs(last_SSE - o_SSE) < TThreshold): break
            last_SSE = o_SSE
        # print(iterations, o_SSE, np.hstack([vA, vx0, vy0, vsigma_x, vsigma_y]))
        return iterations, o_SSE, np.hstack([vA, vx0, vy0, vsigma_x, vsigma_y, vA0])

    def compute_tactile(self, dftgs, optgs, SPACING, GRID, HEIGHT = 0.0):
        cell_interval = SPACING * 0.0001
        DX = - (optgs[:, 1] - dftgs[:, 1]) * cell_interval
        DY = - (optgs[:, 2] - dftgs[:, 2]) * cell_interval
        DZ = - (optgs[:, 0] - dftgs[:, 0]) * cell_interval
        distactile = np.zeros((len(GRID) * len(GRID), 6))
        xv, yv = np.meshgrid(GRID, GRID)
        distactile[:, 0] = xv.flatten() * cell_interval
        distactile[:, 1] = yv.flatten() * cell_interval
        distactile[:, 2] = HEIGHT
        distactile[:, 3] = DX
        distactile[:, 4] = DY
        distactile[:, 5] = DZ

        return distactile # matrix of {ox, oy, oz, dx, dy, dz}


if __name__ == '__main__':
    rospy.init_node('manitactile_node', anonymous=True)
    app = ManiTactile()
    rospy.spin()