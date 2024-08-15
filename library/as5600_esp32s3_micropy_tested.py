"""
# Based on the original file, I tested some functions, and this is a version that can be used directly.
# Example, hope it helps😀
from machine import SoftI2C, Pin
i2c = SoftI2C(scl=Pin(5), sda=Pin(4), freq=600000)
class MyAS5600():
    
    def __init__(self, i2c):
        import as5600
        self.i2c = i2c
        self.device = as5600.AS5600(i2c_device=i2c, hyst=1)
    
    def get_angle(self, fast=False):
        if fast:
            return self.device.getAngleDegreesFast()
        else:
            return self.device.getAngleDegrees()
"""


class AS5600:
    """
    A class for the AS5600 Magnetic Rotary Position Sensor
    """

    ADDRESS     = 0x36  # as5600 is 0x36, as5600l is 0x40

    CONF_REG    = 0x07
    STATUS_REG  = 0x0B
    ANGLE_REG   = 0x0E
    AGC_REG     = 0x1A

    def __init__(self, i2c_device, hyst = 0, powerMode = 0, watchdog = 0,
                 fastFilterThreshold = 0, slowFilter = 0, pwmFreq = 0, outputStage = 0) -> None:
        """Init

        Args:
            hyst (int, optional): Hysteresis: 0->3. Defaults to 0.
            powerMode (int, optional): Power Mode: 0->3. Defaults to 0.
            watchdog (int, optional): Enable the watchdog. Defaults to 0.
            fastFilterThreshold (int, optional): Threshold value for the fast filter: 0->7. Defaults to 0.
            slowFilter (int, optional): Slow filter mode: 0->3. Defaults to 0.
            pwmFreq (int, optional): Output PWM frequency: 0->3. Defaults to 0.
            outputStage (int, optional): Output mode (see datasheet): 0->2. Defaults to 0.
        """
        self.i2c = i2c_device
        c1 = 0x00
        c2 = 0x00

        # set watchdog 0,1
        if watchdog in range(0,2):
            c1 = c1 | (watchdog << 5)

        # set fast filter threshold 0->7
        if fastFilterThreshold in range(0,8):
            c1 = c1 | (fastFilterThreshold << 2)

        # set the slow filter 0->3
        if slowFilter in range(0,4):
            c1 = c1 | slowFilter

        # set PWM frequency 0->3
        if pwmFreq in range(0,4):
            c2 = c2 | (pwmFreq << 6)

        # set output stage 0->2
        if outputStage in range(0,2):
            c2 = c2 | (outputStage << 4)

        # set PowerMode 0->3
        if powerMode in range(0, 4):
            c2 = c2 | powerMode

        # set Hysteresis 0->3
        if hyst in range(0, 4):
            c2 = c2 | (hyst << 2)

        self.i2c.writeto(self.ADDRESS, bytes([self.CONF_REG, c1, c2]))


    def getStatus(self):
        """Get the status of the AS5600

        Returns:
            Dict: Dictionary of the different statuses
        """
        self.i2c.writeto(self.ADDRESS, bytes([self.STATUS_REG]))
        status = int.from_bytes(self.i2c.readfrom(self.ADDRESS, 1), 'big')
        mh = bool(status & 0b00001000)
        ml = bool(status & 0b00010000)
        md = bool(status & 0b00100000)

        self.i2c.writeto(self.ADDRESS, bytes([self.AGC_REG]))
        agc = int.from_bytes(self.i2c.readfrom(self.ADDRESS, 1), 'big')

        return {
                 "magnetDetected": md, 
                 "magnetTooWeak": ml, 
                 "magnetTooStrong": mh,
                 "agc": agc
                 }

    def isOk(self) -> bool:
        """Reads the status values to determine if the magnet is able to be read.

        Returns:
            bool: True if the magnet can be detercted accurately
        """
        self.i2c.writeto(self.ADDRESS, bytes([self.STATUS_REG]))
        status = int.from_bytes(self.i2c.readfrom(self.ADDRESS, 1), 'big')

        mh = bool(status & 0b00001000)
        ml = bool(status & 0b00010000)
        md = bool(status & 0b00100000)

        if md and not mh and not ml:
            return True
        else:
            return False


    def getAngle(self) -> int:
        """Get the raw 12bit angle value

        Returns:
            int: 0->4095
        """
        self.i2c.writeto(self.ADDRESS, bytes([self.ANGLE_REG]))
        return int.from_bytes(self.i2c.readfrom(self.ADDRESS, 2), 'big')
        
        
        
    def getAngleDegrees(self):
        """Get the angle in degrees, IF the magnet can be read

        Returns:
            float: Degrees (0->359) if magnet can be read otherwise None.
        """
        if self.isOk():
            return (float(self.getAngle()) / 4096) * 360
        else:
            # if the magnet cannot be read then the angle is unreliable, so return None.
            return None

    def getAngleDegreesFast(self):
        """Get the angle in degrees

        Returns:
            float: Degrees (0->359) if magnet can be read otherwise None.
        """
        self.i2c.writeto(self.ADDRESS, b'\x0e')
        return (float(int.from_bytes(self.i2c.readfrom(self.ADDRESS, 2), 'big')) / 4096) * 360


    def getConf(self):
        """Internal healper function to read the raw config value

        Returns:
            int: raw value
        """
        self.i2c.writeto(self.ADDRESS, bytes([self.CONF_REG]))
        return int.from_bytes(self.i2c.readfrom(self.ADDRESS, 2), 'big')
