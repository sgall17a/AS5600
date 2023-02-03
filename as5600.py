from machine import I2C,Pin
from micropython import const
from ustruct import unpack, pack
from collections import namedtuple
from time import sleep

AS5600_id = const(0x36)  #Device ID
m12 = const((1<<12)-1)  #0xFFF



REGS=namedtuple('REGS','ZMCO ZPOS MPOS MANG CONF RAWANGLE ANGLE  STATUS AGC MAGNITUDE BURN')
r = REGS(0,1,3,5,7,0xc,0xe,0xb,0x1a,0x1b,0xff)
    
#You cant overwrite __attribute__ in micropython but you can use Descriptors
class RegDescriptor:
    "Read and write a bit field from a register"
    
    def __init__(self,reg,shift,mask,buffsize=2):
        "initialise with specific identifiers for the bit field"

        self.reg = reg
        self.shift = shift
        self.mask = mask
        self.buffsize = buffsize
        self.writeable = (r.ZMCO,r.ZPOS,r.MPOS,r.MANG,r.CONF,r.BURN)
        #NB the I2c object and the device name come from the main class via an object
        
    def get_register(self,obj):
        "Read an I2C register"
        #cache those registers with values that will not change.
        #Dont bother caching bit fields.
        if self.reg in obj.cache:  
             return obj.cache[self.reg]
            
        #print ('reading now the actual device now')
            
        buff = obj.i2c.readfrom_mem(obj.device,self.reg,self.buffsize)
  

        if self.buffsize == 2:
            v = unpack(">H",buff)[0]  #2 bytes big endian
        else:
            v = unpack(">B",buff)[0]
        
            
        #cache writeable values since they are the ones that will not change in useage    
        if self.reg in self.writeable:
            obj.cache[self.reg] = v
            
        return v
        
    def __get__(self,obj,objtype):
        "Get the register then extract the bit field"
        v = self.get_register(obj)
        if self.reg == 11:
            print(self.reg,self.shift,self.mask)
        v >>= self.shift
        v &= self.mask
        return v
    
    def __set__(self,obj,value):
        "Insert a new value into the bit field of the old value then write it back"
        if not self.reg in self.writeable:
            raise AttributeError('Register is not writable')
        oldvalue = self.get_register(obj)
        #oldvalue <<= self.shift # get_register() does a shift, so we have to shift it back
        insertmask = 0xffff - (self.mask << self.shift) #make a mask for a hole
        oldvalue &= insertmask # AND a hole in the old value
        value &= self.mask # mask our new value in case it is too big
        value <<= self.shift
        oldvalue |= value  # OR the new value back into the hole
        if self.buffsize == 2:
            buff = pack(">H",oldvalue)
        else:
            buff = pack(">B",oldvalue)
            
        obj.i2c.writeto_mem(obj.device,self.reg,buff) # write result back to the AS5600
        
        #must write the new value into the cache
        self.cache[self.reg] = oldvalue
        
  

class AS5600:
    def __init__(self,i2c,device):
        self.i2c = i2c
        self.device = device
        self.writeable =(r.ZMCO,r.ZPOS,r.MPOS,r.MANG,r.CONF,r.BURN)
        self.cache = {} #cache register values
        
    #Use descriptors to read and write a bit field from a register
    #1. we read one or two bytes from i2c
    #2. We shift the value so that the least significant bit is bit zero
    #3. We mask off the bits required  (most values are 12 bits hence m12)
    ZMCO=      RegDescriptor(r.ZMCO,shift=0,mask=3,buffsize=1) #2 bit
    ZPOS=      RegDescriptor(r.ZPOS,0,m12) #zero position
    MPOS=      RegDescriptor(r.MPOS,0,m12) #maximum position
    MANG=      RegDescriptor(r.MANG,0,m12) #maximum angle (alternative to above)
    #Dummy example how how to make friendlier duplicate names if you want to
    #max_angle = RegDescriptor(r.MANG,0,m12) #maximum angle (alternative to above)
    CONF=      RegDescriptor(r.CONF,0,(1<<14)-1) # this register has 14 bits (see below)
    RAWANGLE=  RegDescriptor(r.RAWANGLE,0,m12) 
    ANGLE   =  RegDescriptor(r.ANGLE,0,m12) #angle with various adjustments (see datasheet)
    STATUS=    RegDescriptor(r.STATUS,0,m12) #basically strength of magnet
    AGC=       RegDescriptor(r.AGC,0,0xF,1) #automatic gain control
    MAGNITUDE= RegDescriptor(r.MAGNITUDE,0,m12) #? something to do with the CORDIC for atan RTFM
    BURN=      RegDescriptor(r.BURN,0,0xF,1)

    #Configuration bit fields
    PM =      RegDescriptor(r.CONF,0,0x3) #2bits Power mode
    HYST =    RegDescriptor(r.CONF,2,0x3) # hysteresis for smoothing out zero crossing
    OUTS =    RegDescriptor(r.CONF,4,0x3) # HARDWARE output stage ie analog (low,high)  or PWM
    PWMF =    RegDescriptor(r.CONF,6,0x3) #pwm frequency
    SF =      RegDescriptor(r.CONF,8,0x3) #slow filter (?filters glitches harder) RTFM
    FTH =     RegDescriptor(r.CONF,10,0x7) #3 bits fast filter threshold. RTFM
    WD =      RegDescriptor(r.CONF,13,0x1) #1 bit watch dog - Kicks into low power mode if nothing changes
    
    #status bit fields. ?having problems getting these to make sense
    MH =      RegDescriptor(r.STATUS,3,0x1,1) #2bits  Magnet too strong (high)
    ML =      RegDescriptor(r.STATUS,4,0x1,1) #2bits  Magnet too weak (low)
    MD =      RegDescriptor(r.STATUS,5,0x1,1) #2bits  Magnet detected
    
    def scan(self):
        "Debug utility function to check your i2c bus"
        devices = self.i2c.scan()
        print(devices)
        if AS5600_id in devices:
            print('Found AS5600 (id =',hex(AS5600_id),')')
        print(self.CONF)
        
    def burn_angle(self):
        "Burn ZPOS and MPOS -(can only do this 3 times)"
        self.BURN = 0x80
        
    def burn_setting(self):
        "Burn config and mang- (can only do this once)"
        self.BURN = 0x40
    
    def magnet_status(self):
        s = "Magnet "
       # print(self.MD)
        return
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

  
z = AS5600(i2c,AS5600_id)
z.scan()
whatever = 89
while True:
    print(z.MD)
    sleep(1)
    

