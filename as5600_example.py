from time import sleep
from as5600 import *

    

#The class AS5600 is pretty low level.
# This inherits adds some higher level functions
    
class AS5600_high(AS5600):
    
    def __init__(self,i2c,device):
        super().__init__( i2c,device)
    
    def scan(self):
        "Debug utility function to check your i2c bus"
        devices = self.i2c.scan()
        print(devices)
        if AS5600_id in devices:
            print('Found AS5600 (id =',hex(AS5600_id),')')
        print(self.CONF)
        
    def burn_angle(self):
        "Burn ZPOS and MPOS -(can only do this 3 times)"
        #uncomment if you need it
        #self.BURN = 0x80
        
    def burn_setting(self):
        "Burn config and mang- (can only do this once)"
        #uncomment if you need it
        #self.BURN = 0x40
    
    def magnet_status(self):
        "Magnet status - this does not seem to make sense ? why"
        s = "Magnet "

        if self.MD == 1:
            s += " detected"
        else:
            s += " not detected"
            
        if self.ML == 1:
            s+ " (magnet too weak)"
            
        if self.MH == 1:
            s+ " (magnet too strong)"
        return s
    

i2c = I2C(0,scl=Pin(17),sda=Pin(16),freq=400000)        

  
z = AS5600_high(i2c,AS5600_id)
z.scan()

#read write
#This will probably make your device crazy.  Just poweron/poweroff
z.CONF = 0x38
sleep(2)
print ("should be 0x38", hex(z.CONF))
sleep(5)
z.CONF = 0x64
print ("should be 0x64", hex(z.CONF)    )   
    

for i in range(10):
    #print(z.magnet_status())
    print ('ZANGLE',z.RAWANGLE)
    print ('ANGLE', z.ANGLE)
    print ('Magnet detected',z.MD)
    sleep(1)