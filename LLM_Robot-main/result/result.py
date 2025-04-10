#!/usr/bin/env python
# coding:utf-8
from move import *
from slam import *
from nav import *
from find import *
from pick import *
rospy.init_node('control_the_robot', anonymous=True)

nav_ctrl = navigation()
x,y = compute_base_link_position(coordinates[0],coordinates[1])
nav_ctrl.PubTargetPoint(x,y)

arm_ctrl = ArmController()
arm_ctrl.pick_up()

nav_ctrl.PubTargetPoint(0,0)


rospy.spin()

