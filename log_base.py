#!/usr/bin/env python
#-*-  coding: utf-8  -*-
import time
import logging
import sys
import os

from logging import config
class MyLog(object):
 def __init__(self):
  if not os.path.isdir("logs"):
      os.mkdir("logs")
  config.fileConfig(os.path.split(os.path.realpath(__file__))[0] +'/logger.ini')
  self.logger = logging.getLogger('example01')
 def my_logger(self):
  return self.logger