from struct import pack,unpack
from micropython import const


R =True
W=False
   
class Tdesc:
    def __init__(self,readonly,register,firstbit,lastbit):

        self.readonly = readonly
        self.reg = register
        self.mask = (2<<(lastbit-firstbit))-1
        self.punch = (self.mask << firstbit) ^ 0xffff
        if lastbit > 7:
            self.buff = bytearray(2)
            self.packstr = "<H"
        else:
            self.buff = bytearray(1)
            self.packstr="B"
        self.shift = firstbit

    def __get__(self,obj,clss):
        
        obj.I2C.readfrom_mem_into(obj.i2cCode,self.reg,self.buff )
        value = unpack(self.packstr,self.buff)[0]     
        return value & self.mask
           
    def __set__(self,obj,value):
        if self.readonly:
            return
        #dont allow burn reg = 255 to occur here
        if self.reg > 0x1C:
            return
        obj.I2C.readfrom_mem_into(obj.i2cCode,self.reg,self.buff )
        
        old = unpack(self.packstr,self.buff)[0]
        vshift = (value & self.mask)  << self.shift
        newvalue =  (old  & self.punch) | vshift
        mybuff = pack(self.packstr,newvalue)

        obj.I2C.writeto_mem(obj.i2cCode,self.reg,mybuff)
     

class AS5600:
    def __init__(self,i2c,code=54):        
        self.I2C       = i2c
        self.i2cCode   = code
    #M12 = (2<<12)-1  #mask for angle
    ZMCO      = Tdesc(R,0x0,0,1 )  #shift 0  mask = 3
    ZPOS      = Tdesc(W,0x1,0,11)  
    MPOS      = Tdesc(W,0x3,0,11)
    MANG      = Tdesc(W,0x5,0,11)
    CONF      = Tdesc(W,0x7,0,13)  # Bitfields.  Broken out below
 
    RAWANGLE  = Tdesc(R,0xC,0,11)
    ANGLE     = Tdesc(R,0xE,0,11)
    STATUS    = Tdesc(R,0xB,3,5)   # shift 2 mask = 7
    MD        = Tdesc(R,0xB,5,5)
    ML        = Tdesc(R,0xB,4,4)
    MH        = Tdesc(R,0xB,3,3)    
    AGC       = Tdesc(R,0x1A,0,7)
    MAGNITUDE = Tdesc(R,0x1B,0,11)
  
    CONF      = Tdesc(W,0x7,0,13)  # Bitfields.  Broken out below
    WD        = Tdesc(W,0x07,5,5)
    FTH       = Tdesc(W,0x07,2,4)
    SF        = Tdesc(W,0x07,0,1) 
    PWMF      = Tdesc(W,0x08,6,7)
    OUTS      = Tdesc(W,0x08,4,5)
    HYST      = Tdesc(W,0x08,2,3)
    PM        = Tdesc(W,0x08,0,1)
    #BURN_ANGLE        = Tdesc(W,0xFF,5,5)
    #BURN_SETTING      = Tdesc(W,0xFF,6,6)
     
    def burn_angle():
        
        if not self.MD:
            raise 'Can only write angle if magnet detected'
        self.I2C.writeto_mem(obj.i2cCode,255,0x40)
        
    def burn_angle():
        if self.ZMCO:
            raise 'Error. Angle already written'
        self.I2C.writeto_mem(obj.i2cCode,255,0x80)
        