ifndef NEURAL_MODELLING_DIRS
    $(error NEURAL_MODELLING_DIRS is not set.  Please define NEURAL_MODELLING_DIRS (possibly by running "source setup" in the neural_modelling folder within the sPyNNaker source folder))
endif

BUILD_DIR = build/
ifdef TESTING_RESOLUTION
  APP := breakout_test
  SOURCES = bkout_test.c
else
  APP := breakout
  SOURCES = bkout.c
endif

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
CURRENT_DIR := $(dir $(MAKEFILE_PATH))
EXTRA_SRC_DIR := $(abspath $(CURRENT_DIR))
SOURCE_DIRS += $(EXTRA_SRC_DIR)
APP_OUTPUT_DIR := $(abspath $(CURRENT_DIR)../model_binaries/)/
CFLAGS += -I$(NEURAL_MODELLING_DIRS)/src

include $(NEURAL_MODELLING_DIRS)/src/Makefile.common
