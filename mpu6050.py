#
# This file is part of MicroPython MPU9250 driver
# Copyright (c) 2018 Mika Tuupola
#
# Licensed under the MIT license:
#   http://www.opensource.org/licenses/mit-license.php
#
# Project home:
#   https://github.com/tuupola/micropython-mpu9250
#

"""
MicroPython I2C driver for MPU9250 9-axis motion tracking device
"""

import ustruct # pylint: disable=import-error
from machine import I2C, Pin # pylint: disable=import-error
from micropython import const # pylint: disable=import-error

_GYRO_CONFIG = const(0x1b)
_ACCEL_CONFIG = const(0x1c)
_ACCEL_CONFIG2 = const(0x1d)
_INT_PIN_CFG = const(0x37)
_ACCEL_XOUT_H = const(0x3b)
_ACCEL_XOUT_L = const(0x3c)
_ACCEL_YOUT_H = const(0x3d)
_ACCEL_YOUT_L = const(0x3e)
_ACCEL_ZOUT_H = const(0x3f)
_ACCEL_ZOUT_L= const(0x40)
_TEMP_OUT_H = const(0x41)
_TEMP_OUT_L = const(0x42)
_GYRO_XOUT_H = const(0x43)
_GYRO_XOUT_L = const(0x44)
_GYRO_YOUT_H = const(0x45)
_GYRO_YOUT_L = const(0x46)
_GYRO_ZOUT_H = const(0x47)
_GYRO_ZOUT_L = const(0x48)
_WHO_AM_I = const(0x75)

#_ACCEL_FS_MASK = const(0b00011000)
ACCEL_FS_SEL_2G = const(0b00000000)
ACCEL_FS_SEL_4G = const(0b00001000)
ACCEL_FS_SEL_8G = const(0b00010000)
ACCEL_FS_SEL_16G = const(0b00011000)

_ACCEL_SO_2G = 16384 # 1 / 16384 ie. 0.061 mg / digit
_ACCEL_SO_4G = 8192 # 1 / 8192 ie. 0.122 mg / digit
_ACCEL_SO_8G = 4096 # 1 / 4096 ie. 0.244 mg / digit
_ACCEL_SO_16G = 2048 # 1 / 2048 ie. 0.488 mg / digit

#_GYRO_FS_MASK = const(0b00011000)
GYRO_FS_SEL_250DPS = const(0b00000000)
GYRO_FS_SEL_500DPS = const(0b00001000)
GYRO_FS_SEL_1000DPS = const(0b00010000)
GYRO_FS_SEL_2000DPS = const(0b00011000)

# Used for enablind and disabling the i2c bypass access
_I2C_BYPASS_MASK = const(0b00000010)
_I2C_BYPASS_EN = const(0b00000010)
_I2C_BYPASS_DIS = const(0b00000000)

SF_G = 1
SF_SI = 9.80665 # 1 g = 9.80665 m/s2 ie. standard gravity

class MPU6050:
    """Class which provides interface to MPU6050 6-axis motion tracking device."""
    def __init__(
        self, i2c, address=0x68,
        accel_fs=ACCEL_FS_SEL_2G, gyro_fs=GYRO_FS_SEL_250DPS,
        sf=SF_SI
    ):
        self.i2c = i2c
        self.address = address

        if 0x71 != self.whoami:
            raise RuntimeError("MPU6x50 not found in I2C bus.")

        self._accel_fs(accel_fs)
        self._sf = sf

        # Enable I2C bypass to access for MPU9250 magnetometer access.
        char = self._register_char(_INT_PIN_CFG)
        char &= ~_I2C_BYPASS_MASK # clear ODR bits
        char |= _I2C_BYPASS_EN
        self._register_char(_INT_PIN_CFG, char)

    @property
    def acceleration(self):
        """
        Acceleration measured by the sensor. By default will return a
        3-tuple of X, Y, Z axis acceleration values in m/s^2 as floats. Will
        return values in g if constructor was provided `sf=SF_G` parameter.
        """
        so = self._accel_so
        sf = self._sf

        x = self._register_word(_ACCEL_XOUT_H) / so * sf
        y = self._register_word(_ACCEL_YOUT_H) / so * sf
        z = self._register_word(_ACCEL_ZOUT_H) / so * sf
        return (x, y, z)

    @property
    def gyro(self):
        """
        x, y, z radians per second as floats
        """
        return (0.0, 0.0, 0.0)

    @property
    def whoami(self):
        """ Value of the whoami register. """
        return self._register_char(_WHO_AM_I)

    def _register_word(self, register, value=None):
        if value is None:
            data = self.i2c.readfrom_mem(self.address, register, 2)
            return ustruct.unpack(">h", data)[0]
        data = ustruct.pack(">h", value)
        return self.i2c.writeto_mem(self.address, register, data)

    def _register_char(self, register, value=None):
        if value is None:
            return self.i2c.readfrom_mem(self.address, register, 1)[0]
        data = ustruct.pack("<b", value)
        return self.i2c.writeto_mem(self.address, register, data)

    def _accel_fs(self, value):
        self._register_char(_ACCEL_CONFIG, value)

        # Store the sensitivity divider
        if ACCEL_FS_SEL_2G == value:
            self._accel_so = _ACCEL_SO_2G
        elif ACCEL_FS_SEL_4G == value:
            self._accel__so = _ACCEL_SO_4G
        elif ACCEL_FS_SEL_8G == value:
            self._accel_so = _ACCEL_SO_8G
        elif ACCEL_FS_SEL_16G == value:
            self._accel_so = _ACCEL_SO_16G