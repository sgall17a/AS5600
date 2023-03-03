from machine import I2C,Pin
from micropython import const
from ustruct import unpack, pack
from time import sleep

AS5600_id = const(0x36)  #Device ID
m12 = const((1<<12)-1)  #0xFFF  (Frequently used mask value for 12 bits)

#Name the registers according to the datasheet
REGS = const(0)
ZMCO = const(0)
ZPOS = const(1)
MPOS = const(3)
MANG = const(5)
CONF = const(0x7)
RAWANGLE = const(0xC)
ANGLE    = const(0xE)
STATUS   = const(0x1B)
AGC      = const(0x1A)
MAGNITUDE= const(0x1B)
BURN     = const(0xFF)

class AS5600:
    def __init__(self,i2c,device=AS5600_id):
        self.i2c = i2c
        #Device ID shouldnt change unless we remap device ID number say by an id remapping board
        self.device = device

    def readwrite(self,register, firstbit,lastbit,*args):
        "Read and write 1 or 2 bytes with bit fields. (Covers all requirements)"
        #shift = lastbit
        byte_num = 2 if firstbit > 7 else 1  # shift  <= lastbit
        mask = 1<<(firstbit-lastbit+1)-1 #mask is 1 bits same length as value
        b = self.i2c.readfrom(register, bytes) #b is a buffer ie array of 8 bit numbers
        if byte_num == 2:
            oldvalue = b[1]<<8+b[0] & mask
        elif byte_num == 1:
            oldvalue =  b[0] & mask
        else:
            raise('Can only read or write 1 or 2 bytes')
  
        if len(args) == 0:   # No value to write - so just return the value we just read
            return oldvalue

        elif len(args) == 1: #Value is present so pack as bitfield and write
            hole = ~(mask << lastbit) #move value along and invert it
            newvalue = (oldvalue & hole) | ((value & mask)<<lastbit)
            if byte_num ==1:
                bytes2write = bytes([oldvalue])
            else:
                bytes2write = bytes([oldvalue >>8, oldvalue] )
            self.i2c.writeto(register,bytes2write) # write result back to the device
            return value  #Value should now be what we have written
        else:
            raise("Read write can only have 0 or 1 values")

    def zmco(self,value=None):
        "No of times zero angle has been burnt"
        return self.readwrite(ZMCO,1,0,*args)

    def zpos(self,*args):
        "zero position - eg when used as a potentiometer"
        return self.readwrite(ZPOS,11,0,*args)

    def mpos(self,*args):
        "maximum position - eg when used as a potentimeter"
        return self.readwrite(MPOS,11,0,*args)

    def mang(self,*args):
        "maximum angle (alternative to mpos-see mpos)"
        return self.readwrite(MANG,11,0,*args)

# CONFIGURATION From Figure 22 in datasheet

# PM(1:0)     1:0     Power Mode      00 = NOM, 01 = LPM1, 10 = LPM2, 11 = LPM3
# HYST(1:0)   3:2     Hysteresis      00 = OFF, 01 = 1 LSB, 10 = 2 LSBs, 11 = 3 LSBs
# OUTS(1:0)   5:4     Output Stage    00 = analog (full range from 0% to 100% between GND and VDD, 01 = analog (reduced range from 10% to 90% between GND and VDD, 10 = digital PWM
# PWMF(1:0)   7:6     PWM Frequency   00 = 115 Hz; 01 = 230 Hz; 10 = 460 Hz; 11 = 920 Hz
# SF(1:0)     9:8     Slow Filter     00 = 16x (1); 01 = 8x; 10 = 4x; 11 = 2x
# FTH(2:0)    12:10   Fast Filter Threshold   000 = slow filter only, 001 = 6 LSBs, 010 = 7 LSBs, 011 = 9 LSBs,100 = 18 LSBs, 101 = 21 LSBs, 110 = 24 LSBs, 111 = 10 LSBs
# WD          13      Watchdog        0 = OFF, 1 = ON

    def pm(self,value):
        "Power mode - 4 modes see Datas"
        return  self.readwrite(CONF,1,0)
    
    def hyst(self,value):
        "Hysteresis - 0,1,2 or 3 LSB"
        return  self.readwrite(CONF,3,2)

    def outs(self,value):
        "PMW vs Analog 0=Analog, 1= PWM"
        return  self.readwrite(CONF,5,4,*args)
    
    def pwmf(self,*args):
        "PMW frequency 115,230,460 or 920Hz"
        return  self.readwrite(CONF,7,6,*args)

    def sf(self,*args):
        "Slow filter value"
        return  self.readwrite(CONF,9,8,*args)
       
    def fth(self,*args):
        "Fast filter threshold"
        return self.readwrite(CONF,12,10,*args)

    def watchdog(self,*args):
        "Watchdog 0 == OFF< 1 == ON"
        return  self.readwrite(CONF,13,13,*args) 

#output registers - Read only so there is no value supplied in readwrite

    def rawangle(self):
        "Raw angle, no filter, rescaling etc"
        return self.readwrite(RAWANGLE,11,0)

    def angle(self):
        "Angle with hysteresis, etc"
        return self.readwrite(ANGLE,11,0)

#Status registers - Read only
    def md(self):
        "Magnet detected"
        return self.readwrite(STATUS,5,5)

    def ml(self):
        "Magnet too low"
        return self.readwrite(STATUS,4,4)

    def mh(self):
        "Magnet too high"
        return self.readwrite(STATUS,3,3)

    def agc(self):
        "Automatic gain"
        return self.readwrite(AGC,7,0)       

    def magnitude(self):
        "? something to do with the CORDIC (?Dont worry about it)"
        return  self.readwrite(MAGNITUDE,11,0) 

    # Read datasheet before using these functions!!!
    #Permanently burn zpos and mpos values into device (Can only use 3 times)
        
    def burn_angle(self):
        "Burn ZPOS and MPOS -(can only do this 3 times)"
        self.readwrite(BURN,7,0,8) # This wrt
        
    def burn_setting(self):
        "Burn config and mang- (can only do this once)"
        self.readwrite(BURN,7,0,4)

    def scan(self):
        "Debug utility function to check your i2c bus"
        devices = self.i2c.scan()
        print(devices)
        if self.id in devices:
            print('Found AS5600 (id =',hex(self.id),')')
        print(self.CONF)
                  
i2c = I2C(0,scl=Pin(17),sda=Pin(16),freq=400000)        

z = AS5600(i2c)
z.scan()
whatever = 89
while True:
    print(z.MD)
    sleep(1)
    
