from smbus2 import SMBus, i2c_msg # Import thư viện điều khiển I2C
import time # Import để dùng hàm sleep (trễ)

DEVICE_ADDRESS = 0x50 # Địa chỉ "nhà" của con chip trên đường bus

def write_byte(mem_addr, value):
    with SMBus(1) as bus: # Mở "tuyến đường" số 1
        # mem_addr >> 8: Lấy 8 bit cao (MSB) của địa chỉ 16-bit
        # mem_addr & 0xFF: Lấy 8 bit thấp (LSB) của địa chỉ 16-bit
        # Dữ liệu gửi đi là một danh sách: [Địa chỉ cao, Địa chỉ thấp, Giá trị cần lưu]
        data = [mem_addr >> 8, mem_addr & 0xFF, value]
        
        msg = i2c_msg.write(DEVICE_ADDRESS, data) # Tạo một gói tin "Ghi"
        bus.i2c_rdwr(msg) # Thực hiện gửi gói tin đi
        
        # CỰC KỲ QUAN TRỌNG: EEPROM cần thời gian để "nướng" dữ liệu vào chip.
        # Nếu không nghỉ 10ms (0.01s), lệnh ghi tiếp theo sẽ bị lỗi vì chip đang bận.
        time.sleep(0.01) 

def read_byte(mem_addr):
    with SMBus(1) as bus:
        # Bước 1: Gửi lệnh "Tui muốn đọc ở ô nhớ này" (gửi 2 byte địa chỉ)
        write = i2c_msg.write(DEVICE_ADDRESS, [mem_addr >> 8, mem_addr & 0xFF])
        
        # Bước 2: Chuẩn bị một "giỏ" để đựng 1 byte dữ liệu trả về
        read = i2c_msg.read(DEVICE_ADDRESS, 1)
        
        # Thực hiện kết hợp: Gửi địa chỉ xong rồi Đọc dữ liệu về ngay lập tức
        bus.i2c_rdwr(write, read)
        
        # Dữ liệu trả về dạng list, ta lấy phần tử đầu tiên [0]
        return list(read)[0]

try:
    addr = 0x0010 # Chọn ô nhớ số 16
    val = 88      # Muốn lưu số 88 vào đó
    
    write_byte(addr, val) # Gọi hàm ghi
    result = read_byte(addr) # Gọi hàm đọc để kiểm tra lại
    print(f"Kết quả: {result}")
except Exception as e:
    print(f"Lỗi rồi: {e}") # Bắt lỗi nếu lỏng dây hoặc sai địa chỉ
