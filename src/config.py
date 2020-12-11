# encoding: utf-8
"""
#-------------------------------------------------------------------#
#                   CONFIDENTIAL --- CUSTOM STUDIOS                 #     
#-------------------------------------------------------------------#
#                                                                   #
#                   @Project Name : battery_for_linux_mac_win                 #
#                                                                   #
#                   @File Name    : config.py                      #
#                                                                   #
#                   @Programmer   : lizhen                          #
#                                                                   #  
#                   @Start Date   : 2020/12/10 16:25                 #
#                                                                   #
#                   @Last Update  : 2020/12/10 16:25                 #
#                                                                   #
#-------------------------------------------------------------------#
# Classes:                                                          #
#                                                                   #
#-------------------------------------------------------------------#
"""
import os

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
REPORT_PATH = os.path.join(BASE_PATH, 'report')
TEMPLATES_PATH = os.path.join(BASE_PATH, 'templates')
FILE_PATH = os.path.join(BASE_PATH, 'files')
