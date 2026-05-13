# I2C EEPROM Examples với `smbus2`

Tập hợp các ví dụ thực tế về giao tiếp I2C với EEPROM (AT24C02) sử dụng thư viện `smbus2` trên Raspberry Pi / Linux.

---

## Mục lục

- [Ví dụ 1 — Ghi & đọc số nguyên lớn hơn 255 / số thực (float)](#ví-dụ-1--ghi--đọc-số-nguyên-lớn-hơn-255--số-thực-float)
- [Ví dụ 2 — Page Write: Ghi & đọc nhiều byte liên tiếp](#ví-dụ-2--page-write-ghi--đọc-nhiều-byte-liên-tiếp)
- [Ví dụ 3 — I2C Bus Scanner (tương tự `i2cdetect -y 1`)](#ví-dụ-3--i2c-bus-scanner-tương-tự-i2cdetect--y-1)

---

## Ví dụ 1 — Ghi & đọc số nguyên lớn hơn 255 / số thực (float)

### Code

```python
from smbus2 import SMBus, i2c_msg
import time
import struct

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

def write_number(start_addr, number, fmt='>i'):
    data = list(struct.pack(fmt, number))
    for i, b in enumerate(data):
        write_byte(start_addr + i, b)

def read_number(start_addr, fmt='>i'):
    size = struct.calcsize(fmt)
    raw = bytes([read_byte(start_addr + i) for i in range(size)])
    return struct.unpack(fmt, raw)[0]


write_number(DEVICE_ADDRESS, 290306)
print(read_number(DEVICE_ADDRESS))
```

---

### Giải thích chi tiết

#### Các thư viện

| Thư viện | Mục đích |
|---|---|
| `smbus2` | Ngôn ngữ để Python nói chuyện với phần cứng qua cổng I2C |
| `i2c_msg` | Giúp đóng gói dữ liệu theo đúng chuẩn I2C |
| `time` | Dùng `time.sleep(0.01)` — cho vi xử lý thời gian xử lý; nếu thiếu sẽ gặp `OSError: [Errno 5] Input/output error` |
| `struct` | Tách số lớn thành nhiều byte để lưu vào nhiều ô nhớ liên tiếp |

> **Tại sao cần `struct`?**  
> Một ô nhớ trong EEPROM chỉ lưu được 1 byte (tương đương 0→255). Khi đưa vào số `290306` thì lập tức lỗi vì mỗi ô chỉ chứa tối đa 1 byte. `struct` ra đời với mục đích chính là tách thành 4 byte và sau đó lưu vào 4 ô nhớ tiếp theo.

---

#### Phân biệt 3 loại địa chỉ

Khi muốn viết hoặc đọc một bit trong thanh ghi, chúng ta cần biết **địa chỉ thiết bị (Device Address)** và **địa chỉ ô nhớ**. Cũng giống như đặt hàng trên TikTok Shop — bạn cần ghi địa chỉ theo thứ tự: **TP.HCM → Phường/Xã → Địa chỉ nhà/Tên đường**.

| Tên | Giải thích |
|---|---|
| `DEVICE_ADDRESS` | Địa chỉ của chip EEPROM trên bus I2C (ví dụ: `0x50`) — **không đổi**, khai báo là biến hằng global |
| `mem_addr` | Địa chỉ của **một ô nhớ cụ thể** — dùng cho `write_byte`/`read_byte` khi chỉ thao tác 1 byte |
| `start_addr` | Địa chỉ **bắt đầu của một vùng nhớ** — dùng cho `write_number`/`read_number` khi số chiếm nhiều byte |

> **Tại sao `write_byte` chỉ nhận `mem_addr` mà không nhận `DEVICE_ADDRESS`?**  
> `DEVICE_ADDRESS` thường được khai báo là **biến hằng số (global)** ở đầu file vì nó sẽ không thay đổi trong suốt quá trình chạy. Còn `mem_addr` thì thay đổi liên tục nên nó được đưa vào làm tham số.

**Sự khác biệt giữa `mem_addr` và `start_addr`:**

- **`write_byte` — Ghi 1 byte:** Dữ liệu chỉ là một con số từ 0 đến 255, vừa khít trong một ô nhớ. Chỉ cần xác định duy nhất một vị trí là xong việc.

- **`write_number` — Ghi số lớn:** Một số nguyên như `290306` cần tới 4 byte để lưu trữ. Vì mỗi ô nhớ I2C chỉ chứa được 1 byte, buộc phải "xé nhỏ" con số này ra 4 phần và xếp vào 4 ô nhớ nằm liên tiếp.

  Ví dụ khi `start_addr = 10`, hàm sẽ tự hiểu:

  ```
  Byte 1  →  ô nhớ 10
  Byte 2  →  ô nhớ 11
  Byte 3  →  ô nhớ 12
  Byte 4  →  ô nhớ 13
  ```

  > `start_addr` đóng vai trò là "điểm mốc" để máy tính bắt đầu rải dữ liệu, thay vì "một địa chỉ" duy nhất.

---

#### Hàm `write_byte(mem_addr, value)`

Dùng để ghi một con số (0–255) vào một địa chỉ cụ thể.

```python
with SMBus(1) as bus:
```
Mở cổng I2C số 1. `with` giúp tự động đóng cổng khi xong việc để tránh bị lỗi "busy" cho lần sau.

```python
data = [mem_addr & 0xFF, value]
```
Tạo một gói tin gồm địa chỉ ô nhớ và giá trị cần ghi. `& 0xFF` đảm bảo địa chỉ chỉ nằm trong 1 byte.

```python
msg = i2c_msg.write(DEVICE_ADDRESS, data)
```
"Dán nhãn" cho gói tin là lệnh Ghi tới thiết bị có địa chỉ `0x50`.

```python
bus.i2c_rdwr(msg)
```
Thực hiện gửi gói tin đi.

```python
time.sleep(0.01)
```
> ⚠️ **Cực kỳ quan trọng!** Linh kiện phần cứng cần thời gian (khoảng 5–10ms) để "khắc" dữ liệu vào bộ nhớ vật lý. Nếu thiếu, các lệnh ghi liên tiếp sẽ bị mất dữ liệu.

---

#### Hàm `read_byte(mem_addr)`

Dùng để đọc một byte từ địa chỉ cụ thể.

```python
write = i2c_msg.write(DEVICE_ADDRESS, [mem_addr & 0xFF])
```
Đầu tiên phải "nói" cho thiết bị biết: "Tôi muốn đọc ở ô nhớ X".

```python
read = i2c_msg.read(DEVICE_ADDRESS, 1)
```
Chuẩn bị một "chiếc giỏ" trống để hứng 1 byte trả về.

```python
bus.i2c_rdwr(write, read)
```
Gửi yêu cầu đi và nhận kết quả về cùng lúc.

```python
return list(read)[0]
```
Chuyển dữ liệu từ dạng byte sang con số để Python xử lý.

---

#### Các hàm nâng cao — Thao tác với số lớn

**`write_number(start_addr, number, fmt='>i')`**

| Thành phần | Ý nghĩa |
|---|---|
| `fmt = '>i'` | `>` là Big-endian (số lớn đứng trước), `i` là kiểu Integer (4 byte) |
| `struct.pack(fmt, number)` | Biến số `290306` thành một danh sách 4 byte: `[Byte1, Byte2, Byte3, Byte4]` |
| `enumerate(data)` | Duyệt qua từng byte và gọi `write_byte` để lưu vào các ô nhớ liên tiếp (`start_addr + i`) |

**`read_number(start_addr, fmt='>i')`**

| Thành phần | Ý nghĩa |
|---|---|
| `struct.calcsize(fmt)` | Hỏi xem kiểu dữ liệu `i` này chiếm bao nhiêu ô nhớ (thường là 4) |
| List comprehension | Chạy vòng lặp để thu thập đủ 4 byte từ bộ nhớ |
| `struct.unpack(fmt, raw)[0]` | Ghép 4 byte đó lại thành con số ban đầu |

---

## Ví dụ 2 — Page Write: Ghi & đọc nhiều byte liên tiếp

Thay vì ghi từng byte một, ghi cả một mảng dữ liệu `[1, 2, 3, 4, 5]` vào các ô nhớ liền kề rồi đọc lại.

### Code

```python
from smbus2 import SMBus, i2c_msg
import time

DEVICE_ADDRESS = 0x50
PAGE_SIZE = 8  # AT24C02 mỗi trang 8 bytes

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

# ── Page Write: ghi nhiều byte trong 1 lần ──────────────────────

def write_page(start_addr, data_list):
    page_start = (start_addr // PAGE_SIZE) * PAGE_SIZE
    page_end   = page_start + PAGE_SIZE - 1

    if start_addr + len(data_list) - 1 > page_end:
        print(f"Cảnh báo: Dữ liệu vượt trang! Trang bắt đầu: 0x{page_start:02X}, kết thúc: 0x{page_end:02X}")
        return

    with SMBus(1) as bus:
        payload = [start_addr & 0xFF] + data_list
        msg = i2c_msg.write(DEVICE_ADDRESS, payload)
        bus.i2c_rdwr(msg)
        time.sleep(0.01)

def read_many(start_addr, length):
    raw = [read_byte(start_addr + i) for i in range(length)]
    return raw

# ── Test ────────────────────────────────────────────────────────

try:
    data  = [1, 2, 3, 4, 5, 6, 7, 8]  # 8 bytes, vừa đúng 1 trang
    START = 0x10

    print(f"Đang ghi (page write): {data}")
    write_page(START, data)

    print("Đang đọc lại...")
    result = read_many(START, len(data))

    print(f"Kết quả: {result}")
    print(f"Khớp: {data == result}")

except Exception as e:
    print(f"Lỗi: {e}")
```

---

### Giải thích chi tiết

#### Khái niệm Page Boundary

**Page boundary** chính là điểm kết thúc của một trang và bắt đầu của một trang tiếp theo.

Ví dụ: nếu chip EEPROM có kích thước trang là 32 bytes:

```
Trang 0:  địa chỉ   0 →  31
Trang 1:  địa chỉ  32 →  63
          ↑
     page boundary (giữa địa chỉ 31 và 32)
```

> ⚠️ **Hiện tượng Roll-over:** Nếu bạn muốn ghi dữ liệu X, Y, Z nhưng lại bắt đầu từ ô 31, sẽ gặp lỗi **roll-over** (ghi đè lên đầu trang hiện tại thay vì sang trang mới).  
> **Giải pháp:** tính toán địa chỉ trước khi gửi, hoặc chỉ ghi từng byte một (chậm hơn).

**Tại sao có hiện tượng này?** — Đây không phải là lỗi, mà là do thiết kế phần cứng:

- Chip I2C có một bộ đệm nhỏ (Buffer) chỉ bằng đúng kích thước một trang.
- Khi bạn gửi dữ liệu, nó nạp vào Buffer này trước.
- Cái mạch nạp địa chỉ bên trong chip chỉ có khả năng tăng số thứ tự trong phạm vi Buffer đó thôi. Khi chạm mốc cuối (ví dụ 7), nó tự reset về 0 thay vì nhảy sang trang tiếp theo.

---

#### Hàm `write_page(start_addr, data_list)`

**Phần 1 — Tính ranh giới trang hiện tại**

```python
page_start = (start_addr // PAGE_SIZE) * PAGE_SIZE
```

`//` là phép chia lấy phần nguyên, dùng để tìm đầu trang hiện tại.

```
start_addr = 0x10 = 16
PAGE_SIZE  = 8

16 // 8 = 2   → đang ở trang số 2
2  ×  8 = 16  → đầu trang số 2 là địa chỉ 16 (= 0x10)

→ page_start = 0x10
```

```python
page_end = page_start + PAGE_SIZE - 1
```

Cuối trang = đầu trang + 8 ô − 1:

```
page_start = 0x10 = 16
16 + 8 - 1  = 23  = 0x17

→ page_end = 0x17
→ Trang hiện tại trải dài từ 0x10 đến 0x17 (tổng cộng 8 ô)
```

---

**Phần 2 — Kiểm tra có vượt ranh giới không**

```python
if start_addr + len(data_list) - 1 > page_end:
```

Ví dụ ghi `[1, 2, 3, 4, 5]` từ `0x10`:

```
start_addr           = 0x10 = 16
len([1,2,3,4,5]) - 1 = 4          # byte cuối cách đầu 4 ô
ô cuối sẽ ghi vào   = 16 + 4 = 20 = 0x14

0x14 > 0x17 ?  → KHÔNG  ✅ an toàn, tiếp tục ghi
```

Ví dụ ghi `[10,20,30,40,50,60,70,80,90]` (9 bytes) từ `0x10`:

```
ô cuối sẽ ghi vào = 16 + 8 = 24 = 0x18

0x18 > 0x17 ?  → CÓ  ❌ vượt trang, in cảnh báo và return
```

---

**Phần 3 — Đóng gói và ghi 1 lần**

```python
payload = [start_addr & 0xFF] + data_list
```

Ghép địa chỉ vào đầu danh sách data:

```
start_addr & 0xFF = 0x10
data_list         = [1, 2, 3, 4, 5]

payload = [0x10, 1, 2, 3, 4, 5]
#          ↑ địa chỉ  ↑ data
```

Chip nhận gói này, hiểu rằng: "ghi 1 vào 0x10, 2 vào 0x11, 3 vào 0x12..." — tất cả trong 1 lần gửi.

---

#### Hàm `read_many(start_addr, length)`

```python
def read_many(start_addr, length):
    raw = [read_byte(start_addr + i) for i in range(length)]
    return raw
```

`range(length)` sinh ra dãy số từ 0 đến `length - 1`:

```
length = 5
range(5) → [0, 1, 2, 3, 4]

→ đọc lần lượt:
  read_byte(0x10 + 0) = 1
  read_byte(0x10 + 1) = 2
  read_byte(0x10 + 2) = 3
  read_byte(0x10 + 3) = 4
  read_byte(0x10 + 4) = 5

raw = [1, 2, 3, 4, 5]
```

---

#### Phần Test

```python
data  = [1, 2, 3, 4, 5]
START = 0x10
```
Khai báo data muốn ghi và địa chỉ bắt đầu.

```python
write_page(START, data)
```
Ghi cả 5 số trong 1 lần gửi.

```python
result = read_many(START, len(data))
```
`len(data) = 5` → đọc lại đúng 5 ô.

```python
print(f"Khớp: {data == result}")
```
So sánh list với list — Python so sánh từng phần tử một:

```python
[1, 2, 3, 4, 5] == [1, 2, 3, 4, 5]  # → True
[1, 2, 3, 4, 5] == [1, 2, 3, 4, 9]  # → False
```

---

#### Tóm tắt luồng hoạt động

```
data = [1, 2, 3, 4, 5]
          ↓
payload = [0x10, 1, 2, 3, 4, 5]   ← gửi 1 lần lên chip
          ↓
EEPROM:  0x10=1  0x11=2  0x12=3  0x13=4  0x14=5
          ↓
read_many đọc từng ô  →  raw = [1, 2, 3, 4, 5]
```

---

## Ví dụ 3 — I2C Bus Scanner (tương tự `i2cdetect -y 1`)

### Code

```python
from smbus2 import SMBus, i2c_msg
import time


def scan_bus():
    found = []
    with SMBus(1) as bus:
        for addr in range(0x03, 0x78):
            try:
                bus.read_byte(addr)
                found.append(addr)
            except OSError:
                pass
    return found

def print_table(found):
    print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
    for row in range(0, 8):
        line = f"{row * 16:02x}: "
        for col in range(0, 16):
            addr = row * 16 + col
            if addr < 0x08 or addr > 0x77:
                line += "   "
            elif addr in found:
                line += f"{addr:02x} "
            else:
                line += "-- "
        print(line)


try:
    print("Đang quét bus I2C...")
    found = scan_bus()

    print(f"\nTìm thấy {len(found)} thiết bị: {[hex(a) for a in found]}\n")
    print_table(found)

except Exception as e:
    print(f"Lỗi: {e}")
```

---

### Giải thích chi tiết

#### 1. Phần quét Bus — `scan_bus()`

Hãy tưởng tượng I2C Bus là một con phố có các ngôi nhà đánh số từ `0x03` đến `0x77` (tổng cộng khoảng 117 địa chỉ khả dụng).

```python
bus.read_byte(addr)
```
Giống như bạn đến trước cửa nhà số `addr` và gõ cửa.

| Tình huống | Kết quả |
|---|---|
| Có người trả lời (ACK) | Code chạy tiếp, địa chỉ đó được thêm vào danh sách `found` |
| Không có ai (NACK) | Gây ra `OSError` → `except OSError: pass` lờ đi và đi sang nhà tiếp theo |

---

#### 2. Logic tạo bảng — `print_table()`

Mục tiêu: in ra một ma trận **8 hàng × 16 cột** để bao quát toàn bộ 128 địa chỉ (từ `0x00` đến `0x7F`).

**Bước 1 — In dòng tiêu đề (Cột)**

```python
print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
```

Dòng này in thủ công các số từ 0 đến f (hệ Hex) để người dùng biết cột đó là giá trị hàng đơn vị bao nhiêu.

**Bước 2 — Vòng lặp hàng (Row)**

```python
for row in range(0, 8):
    line = f"{row * 16:02x}: "
```

- `range(0, 8)`: Tạo ra 8 hàng (0 đến 7).
- `row * 16`: Tại sao nhân 16? Vì mỗi hàng chứa 16 địa chỉ.

```
Hàng 0 bắt đầu từ  0 × 16 =  0  (Hex: 00)
Hàng 1 bắt đầu từ  1 × 16 = 16  (Hex: 10)
...
```

- `f"{...:02x}: "`: Định dạng số đó dưới dạng Hex 2 chữ số.

**Bước 3 — Vòng lặp cột (Column)**

Trong mỗi hàng, chạy 16 cột với công thức:

```python
addr = row * 16 + col
```

> **Công thức:** `Address = (Hàng × 16) + Cột`
>
> Ví dụ: hàng 1, cột `a` (= 10 trong decimal):  
> `Addr = (1 × 16) + 10 = 26` → Hex là `0x1a`

**Bước 4 — Kiểm tra và in (3 trường hợp)**

| Điều kiện | Kết quả in |
|---|---|
| `addr < 0x08` hoặc `addr > 0x77` | `"   "` (khoảng trắng — vùng reserved của I2C) |
| `addr in found` | `f"{addr:02x} "` (số Hex — thiết bị đang kết nối) |
| Không có ai | `"-- "` (dấu gạch ngang — ô trống) |

---

#### 3. Ví dụ minh họa con số

Giả sử tìm thấy một thiết bị tại địa chỉ `0x12` (thập phân là 18).

Khi vòng lặp chạy đến **Hàng 1** (`row = 1`):
- Đầu dòng in: `10:` (vì `1 × 16 = 16`, đổi sang Hex là `10`)
- Cột 0: `Addr = 16+0 = 16` → Không có trong `found` → In `--`
- Cột 1: `Addr = 16+1 = 17` → Không có trong `found` → In `--`
- Cột 2: `Addr = 16+2 = 18` → **CÓ TRONG FOUND!** (vì `0x12 = 18`) → In `12`
- ... tiếp tục cho đến hết cột `f`

Kết quả dòng đó:

```
10: -- -- 12 -- -- -- -- -- -- -- -- -- -- -- -- --
```

---

#### 4. Tóm tắt các hàm định dạng

| Cú pháp | Giải thích |
|---|---|
| `f"{addr:02x}"` | `:x` = in kiểu Hex; `2` = luôn in 2 chữ số; `0` = thêm số 0 đằng trước nếu thiếu |
| `row * 16` | Nhảy từ địa chỉ `0x00` sang `0x10`, `0x20`, `0x30`... — cách tạo bảng cực kỳ thông minh |
