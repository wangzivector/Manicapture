cmake_minimum_required(VERSION 2.8.3)

project(manicapture)

find_package(catkin REQUIRED COMPONENTS
  dynamic_reconfigure
  std_msgs
  roscpp
  rospy
  sensor_msgs
  # camera_info_manager
  # cv_bridge
  # image_transport
)

find_package(OpenCV REQUIRED)

generate_dynamic_reconfigure_options(
  cfg/machineparams.cfg
)
catkin_package()

include_directories(
  ${catkin_INCLUDE_DIRS}
  # ${OpenCV_INCLUDE_DIRS}
)

# for dynamic reconfigure
add_executable(machine_server src/machine_server.cpp)
# make sure configure headers are built before any node using them
add_dependencies(machine_server ${PROJECT_NAME}_gencfg)
# for dynamic reconfigure
target_link_libraries(machine_server ${catkin_LIBRARIES})

# add_executable(pose_imager_node src/pose_imager.cpp)
# target_link_libraries(pose_imager_node
#   ${catkin_LIBRARIES}
#   ${OpenCV_LIBRARIES}
# )
