from smbus2 import SMBus, i2c_msg
import time

DEVICE_ADDRESS = 0x50

def write_byte(mem_addr, value):
    with SMBus(1) as bus:
        data = [mem_addr & 0xFF, value]          
        msg = i2c_msg.write(DEVICE_ADDRESS, data)
        bus.i2c_rdwr(msg)
        time.sleep(0.01)

def read_byte(mem_addr):
    with SMBus(1) as bus:
        write = i2c_msg.write(DEVICE_ADDRESS, [mem_addr & 0xFF]) 
        read  = i2c_msg.read(DEVICE_ADDRESS, 1)
        bus.i2c_rdwr(write, read)
        return list(read)[0]

# Ghi
write_byte(DEVICE_ADDRESS, 29)

# Đọc
result = read_byte(DEVICE_ADDRESS)
print(result)  
