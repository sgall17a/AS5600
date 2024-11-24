# Micropython library for AS5600

# PLEASE NOTE - There has been a rewrite.  See comments below.  The old file is in old_as5600.py

The AS5600 is an angle sensor, based on detecting  the rotation of a magnet by the Hall effect.  The resolution is 12 bits thus it can divide a complete rotation into 2^12 or 4096 parts. The device is configured and read by I2C.  This library can read all registers on the AS5600 and can write to the writable registers.  (This is a complete rewrite of the library which simplifies the Descriptors used in the previous version)

The device is  configured and read through I2C but can also be used in a standalone mode in 
which the angle is converted either to a voltage between 0 and 3.3V or to a PWM output.  

## Overview.
Notes:  
    1. Relevant register names in brackets.  
    2. The registers can READ/WRITE (congiguration), READONLY(status and readout) or WRITE ONLY (BURN). 
    3. This is a brief overview and the datasheet will need to be consulted for forfurther information).

### Configuration registers (READ/WRITE)   
1.  Setting a minimum and maximum angle. (ZPOS,MPOS,MANG)
2.  Setting an output type, either an analog voltage or duty cycle on a PWM output.  This is mainly for a standalone mode in which the device can be used without a microprocessor. (OUTS)
4.  Set PWM frequency. (PWMF)
3.  Set direction (either clockwise or anti-clockwise). (Pin)
4.  Set power mode to use less current and a watchdog setting.( PM, WD)
5.  Filtering output to reduce jitter, either fast or slow (SF,FTH)
6.  Setting some hysteresis in order to stabilise sensors outputs. (HYST)

### Status registers (Read only):
1.  Magnet strength (MD,ML,MH)
2.  Automatic gain control (adusted automatically bring readings to useable levels) (AGC)

### Reading sensor values (Read only)
Output can be analog, PWM or the register values ANGLE and RAWANGLE.

### Burning configuration.
Configuration can be permanently burnt into the device to enable it to operate in a standalone fashion.
This is down by writing to a burn register. (BURN).
Maximum and minimal angles can only be burnt three times and the burn count is stored in ZMCO.  (See datasheet!)  

## Library
The library provides a class AS5600 in a file called ‘as5600.py’ and is initialised by passing in an I2C object from machine library.   

**Class A5600**

This class is instantiated with an I2C object from the micropython machine library.
An optional device id can be supplied (default 0x36),  say if you had multiple devices and were using a I2C bus multiplexer 

### General notes

Each register is assigned a method with the same name as  the datasheet  except that it is in lower case rather upper case.

If the method is called with no parameter it returns the value of the register

If the method is called with a parameter then the register is set to the value of the parameter and the passed parameter is returned.

If you try to write to a non-writeable register an error will be thrown


# AS5600 rewrite. 

I have rewritten the AS5600p.py.  This is a work in progress because I am learning (slowly) to use Github! 
Register attributes should work the same.  The internal mechanism has changes. 

The scan() utility has been dropped. Just call scan on the I2C object

The method magnet_status has been dropped.  Just use the magnet status attributes.

Burn angle and burn setting have changed a bit.  I did not want to put these as normal attributes to
limit the likelihood of being used inadvertently.

NOTE-I have never actually used BURN  because I dont want to brick my device for programming.

## Notes on internal changes.
Descriptor classes are supported by Micropython.  I think these are more neater and more conventional.  I whas just learing
about descriptors when I wrote the first version.

I dropped the namedtuple.  I think does not actually provide any benefit in conciseness or readability.

Various other simplifications.

I dropped register cacheing.  This was done mainly to limit bitfield extraction from CONF but considering this will only a few times 
(at most) it is not the worth the effort or complication.

### Testing.
I have run a few tests.  These consist of testing reading and writing attributes  with a range of values which seems to work.
Interestingly writing to a register seems to persist through a power cycle (as it should).

Reading values by moving a magnet around and reading from angle and rawangle gives plausible values but I have not made a rig to test the accuracy of results.  Angle results are reasonable.  Rawangle seems too unstable, at least in this setup, to be useable.

### Checking against datasheet.
This is a moderately complex device with both magnetics and electronics.  
This library is not sufficient for documentation of the device and the datasheet should be kept for reference.

The name of the attributes are capitalised versions of the register names in the data sheet.  

I have added a field to the data descriptor classes (R or W) to indicate read and write registers.

There is a chart in the datasheet showing the registers and their bitfields.  My library is derived from this chart.

The smaller bit address and the larger bit address for each bitfield is passed to the descriptor.  The descriptor either reads the bitfields or sets the bitfields and writes the whole adjusted register back to the device.







### Example.


``` python
from as5600 import AS5600
z = AS5600(i2c)
#Read the ZPOS register:  
value = z.zpos(). #This will return the register value
#Write to the ZPOS register  
k = z.pos(value).  #This will return the value supplied, after writing it to the register
```

# All register methods

## Set Angles

``` python 

def zpos(self,*args)
    Zero value, to set that the minimum readout  value
    
def mpos(self,*args)
    Maximum position in devices units or 360/4096.  Setting this clear the maximum angle

def mang(self,*args)
    Set the maximum position in degrees.  Setting this clears the mpos value
```

## Configuration (Read / Write)


``` python
def pm(self,*args)
    """Power Mode.  There are 4 modes to reduce device current at the expense of increasing polling time
    00 = NOM, 
    01 = LPM1 
    10 = LPM2 
    11 = LPM3"""
    
def hyst(sel,*args)
    """Hysteresis.  Set 4 hysteresis modes to reduce output jitter
    00 = OFF,
    01 = 1 LSB, 
    10 = 2 LSBs, 
    11 = 3 LSBs"""
    
def z.outs(self,*args)
    """Output stage PWM or analog
    00 = analog (full range from 0% to 100% between GND and VDD,
    01 = analog (reduced range from 10% to 90% between GND and VDD, 
    10 = digital PWM"""

def pwmf(self,*args)

    """PWM frequency   
    00 = 115 Hz; 
    01 = 230 Hz; 
    10 = 460 Hz; 
    11 = 920 Hz"""

def sf(self,*args )
    """Slow filter to reduce jitter or noise.
     00 = 16x (1); 
     01 = 8x; 
     10 = 4x; 
     11 = 2x"""

def fth(self,*args)
    """Fast filter to reduce jitter or noise
    000 = slow filter only, 
    001 = 6 LSBs, 
    010 = 7 LSBs,
    011 = 9 LSBs,
    100 = 18 LSBs, 
    101 = 21 LSBs, 
    110 = 24 LSBs, 
    111 = 10 LSBs"""

def wd(self,*args)
   """ Watchdog.  Drop into LPM3 after about 1 minute of inactivity
    0 = OFF, 
    1 = ON   """      

```
## Status (Read only )

```python

def md(self)
    #Magnet detected

def ml(self)
    #Magnet too weak
    
def mh(self)   
    # Magnet too strong
    
def agc(self)
    #Automatic Gain control (0-255)
    
```

## Actual angles read only

``` python
def rawangle(self)
    #Raw angle
    
def angle(self)
    #Angle - same as rawangle() but filters and hysteresis applied
```


# Comments.

The library was tested and developed on a Raspberry Pi Pico with Micropython 19.1.1.

Standard micropython is used and this should run on other boards and micropython versions.

I have had trouble using hardware I2C on the Pi Pico but SoftI2C was fine.

Not tested on Circuitypython but I would expect that some fixes and changes may be required. 



