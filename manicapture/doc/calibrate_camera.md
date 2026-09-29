```bash
sudo apt install ros-noetic-camera-calibration

# 1.launch the camara with image topic
# 2.print and fix a checkerboard to a flat surface (the 8x6 board is downloadable at:)
# http://wiki.ros.org/camera_calibration/Tutorials/MonocularCalibration
# 3.run the following calibrator, modify the rect size and image topic 

rosrun camera_calibration cameracalibrator.py --size 8x6 --square 0.025 image:=/camera/image_raw camera:=/camera  --no-service-check

# after collecting enough images, click calibrate, wait tens senconds, ten click save 
# open '/tmp/calibrationdata.tar.gz', extract the ost.yaml 
# change the camra_name inside the yaml as `camera`
# rename ost.yaml as 'camera.yaml' and put in /manicapture/cfg/
```