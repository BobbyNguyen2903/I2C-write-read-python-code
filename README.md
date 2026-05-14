# Hướng dẫn cấu hình I2C & giao tiếp EEPROM AT24C02 trên Raspberry Pi (Ubuntu)

Hướng dẫn từng bước cách bật I2C, cài đặt công cụ, và lập trình đọc/ghi module EEPROM AT24C02 trên Raspberry Pi chạy Ubuntu.

---

## Mục lục

1. [Cấu hình I2C trong boot config](#bước-1--2-cấu-hình-i2c-trong-boot-config)
2. [Kích hoạt module i2c-dev](#bước-3--4-kích-hoạt-module-i2c-dev)
3. [Cài đặt công cụ và phân quyền](#bước-5--7-cài-đặt-công-cụ-và-phân-quyền)
4. [Khởi động lại hệ thống](#bước-8-khởi-động-lại-hệ-thống)
5. [Kiểm tra kết nối module](#bước-9-kiểm-tra-kết-nối-module)
6. [Cài thư viện Python](#bước-10-cài-thư-viện-python)
7. [Viết code đọc/ghi EEPROM](#bước-10-11-viết-code-đọcghi-eeprom)
8. [Chạy thử chương trình](#bước-11--12-chạy-thử-chương-trình)

---

## Bước 1 & 2: Cấu hình I2C trong boot config

Mở file cấu hình của Raspberry Pi:

```bash
sudo nano /boot/firmware/config.txt
```

Tìm dòng sau, nếu chưa có thì thêm vào cuối file:

```
dtparam=i2c_arm=on
```

Lưu file: `Ctrl + O` → `Enter` → thoát: `Ctrl + X`

---

## Bước 3 & 4: Kích hoạt module i2c-dev

Mở file modules:

```bash
sudo nano /etc/modules
```

Thêm dòng sau vào cuối file:

```
i2c-dev
```

Lưu và thoát.

> **Giải thích:** `i2c-dev` tạo ra các file đại diện cho cổng I2C trong thư mục `/dev/`. Nếu không có module này, các phần mềm sẽ không thể giao tiếp với phần cứng I2C.

---

## Bước 5 – 7: Cài đặt công cụ và phân quyền

Trên Ubuntu, mặc định tài khoản của bạn có thể chưa có quyền truy cập trực tiếp vào phần cứng I2C.

### Cài đặt i2c-tools

```bash
sudo apt update
sudo apt install i2c-tools -y
```

> **Giải thích:** `i2c-tools` là bộ công cụ dòng lệnh để chuẩn đoán I2C, bao gồm các lệnh như `i2cdetect`, `i2cget`, `i2cset`. Tham số `-y` tự động đồng ý với tất cả các xác nhận trong quá trình cài đặt.

### Thêm user vào group `i2c`

Để chạy code mà không cần dùng `sudo`:

```bash
sudo adduser $USER i2c
```

---

## Bước 8: Khởi động lại hệ thống

> Đây là bước **bắt buộc** để các thay đổi trong `config.txt` có hiệu lực.

```bash
sudo reboot
```

---

## Bước 9: Kiểm tra kết nối module

Sau khi reboot, cắm dây module AT24C02 vào Raspberry Pi rồi chạy:

```bash
i2cdetect -y 1
```

### Ví dụ output:

```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: 50 -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- -- --    
```

### Giải thích lệnh

**Tại sao dùng `1` mà không phải `20` hay `21`?**

Raspberry Pi 4 có nhiều đường I2C (`i2c-1`, `i2c-20`, `i2c-21`). Số `1` chỉ định kiểm tra các thiết bị đang kết nối vào chân SDA và SCL (các chân vật lý mà bạn đã cắm module vào).

**Cơ chế hoạt động của `i2cdetect`:**

Khi chạy, Raspberry Pi gửi tín hiệu Start Bit kèm địa chỉ (ví dụ `0x50`). Nếu có chip AT24C02 đang cắm tại địa chỉ đó, nó sẽ kéo tín hiệu từ `1 → 0` (ACK) để phản hồi, và địa chỉ đó sẽ hiển thị trong bảng. Nếu không có phản hồi thì hiển thị `--`.

Quá trình này lặp lại từ địa chỉ `0x03` đến `0x77` (tổng cộng 127 lần).

**Tại sao chỉ quét từ `0x03` đến `0x77`?**

Trong giao thức I2C tiêu chuẩn, địa chỉ thiết bị dài 7 bit (2⁷ = 128 địa chỉ, từ `0x00` đến `0x7F`). Tuy nhiên, hiệp hội quản lý chuẩn I2C đã giữ lại một số địa chỉ đặc biệt:
- `0x00 – 0x02`: Dùng cho lệnh *General Call* hoặc lệnh khởi động bus.
- `0x78 – 0x7F`: Dành cho thiết bị đời mới có địa chỉ 10-bit hoặc mục đích thử nghiệm.

Các thiết bị ngoại vi thông thường (EEPROM, cảm biến nhiệt, LCD...) chỉ được phép nằm trong khoảng `0x03` đến `0x77`.

**Cách đọc bảng:**

```
Địa chỉ = hàng + cột

Ví dụ 1: thấy "50" ở hàng 50, cột 0  →  0x50 + 0x00 = 0x50
Ví dụ 2: thấy "68" ở hàng 60, cột 8  →  0x60 + 0x08 = 0x68
```

### Kiểm tra bằng lệnh khác

```bash
ls /dev/*i2c*
```

Output mong đợi:

```
/dev/i2c-1
```

> **Lưu ý:** Kết quả có thể trả về đến 3 cổng: `i2c-1`, `i2c-20`, `i2c-21`. Chỉ cần quan tâm đến `i2c-1` — đây là cổng kết nối vật lý. Hai cổng còn lại (`i2c-20`, `i2c-21`) là cổng I2C nội bộ của Raspberry Pi.

---

## Bước 10: Cài thư viện Python

```bash
sudo apt update
sudo apt install python3-smbus2 -y
```

### Khái niệm "Bus" trong I2C

| | Mô tả |
|---|---|
| **Bus vật lý** | 2 sợi dây (SDA – data, SCL – clock) và bộ điều khiển điện tử trên Pi |
| **Bus trong `smbus2`** | Interface giúp điều khiển 2 sợi dây đó từ code Python |

> **Ví dụ thực tế:** Giống như vô lăng xe hơi — bus vật lý là hệ thống bánh xe và trục lái bên dưới gầm xe, còn hàm trong thư viện là cái vô lăng bạn cầm trên tay. Bạn không cần xuống gầm xe để bẻ lái, chỉ cần xoay vô lăng (gọi hàm Python) là xong.

---

## Bước 10–11: Viết code đọc/ghi EEPROM

Tạo file test:

```bash
nano test_eeprom.py
```
### Source code

```python
from smbus2 import SMBus, i2c_msg
import time

DEVICE_ADDRESS = 0x50

def write_byte(mem_addr, value): #Hai hàm write/read_byte là hai hàm bắt buộc phải có khi muốn viết hoặc ghi một dữ lieuejk 
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
print(result)   #Có thể ghi các giá trị từ 0 -> 255 tương đương 1 byte ~ 8 bit  

```

- **`SMBus`**: Class đại diện cho bus I2C — "người lái xe" điều khiển các tín hiệu điện trên dây.
- **`i2c_msg`**: Công cụ tạo ra các "gói hàng" (messages) có cấu trúc tùy chỉnh. AT24C02 yêu cầu gửi địa chỉ ô nhớ theo cách riêng, nên ta cần công cụ này thay vì các hàm đơn giản có sẵn.
- **`DEVICE_ADDRESS = 0x50`**: "Số nhà" của con chip trên đường bus. Raspberry Pi sẽ phát địa chỉ này lên đường dây để chip phản hồi.

#### 2. Hàm ghi `write_byte`

```python
data = [mem_addr & 0xFF, value]
```

| Thành phần | Giải thích |
|---|---|
| `mem_addr & 0xFF` | **Địa chỉ ô nhớ và giới hạn byte** — đóng vai trò là một bộ lọc (mask) để đảm bảo tính toàn vẹn của giao thức. |
| `value` | Dữ liệu muốn ghi |
| `time.sleep(0.01)` | Chip EEPROM ghi bằng cách thay đổi vật lý electron bên trong, mất ~5–10ms. Nếu không nghỉ, lệnh tiếp theo sẽ bị từ chối (lỗi I/O) |

#### 3. Hàm đọc `read_byte`

Quy trình đọc gồm **2 giai đoạn**:

1. **Chỉ đường (Write):** Pi gửi 1 byte địa chỉ (mem_addr & 0xFF) để báo "tôi muốn đọc ô nhớ số X".
2. **Lấy hàng (Read):** Pi tạo "chiếc giỏ" trống 1 byte để nhận dữ liệu chip trả về.

```python
bus.i2c_rdwr(write, read)
```

Lệnh **Combined Transaction** — thực hiện liên tiếp: gửi địa chỉ → Repeated Start → chuyển sang chế độ nhận dữ liệu.

> `list(read)[0]`: Dữ liệu trả về từ `i2c_msg` là đối tượng byte-array, cần chuyển thành list Python để lấy phần tử đầu tiên.

#### 4. Khối `try...except`

Nếu có sự cố (tuột dây, sai địa chỉ, chip hỏng...), chương trình sẽ không bị crash mà in thông báo lỗi để dễ debug.

---

## Bước 11 & 12: Chạy thử chương trình

```bash
python3 test_eeprom.py
```

### Output mong đợi nếu thành công

```
29
```

Một chương trình đúng phải có khả năng **ghi và đọc lại chính xác** dữ liệu mà người dùng đã đặt vào.

