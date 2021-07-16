from AS5600 import AS5600, AS5600_id
from time import sleep
             

i2c = I2C(0,scl=Pin(17),sda=Pin(16),freq=400000)        

  
z = AS5600(i2c,AS5600_id)
z.scan()
whatever = 89
while True:
    print(z.RAWANGLE)
    print(z.MD)
    sleep(1)
