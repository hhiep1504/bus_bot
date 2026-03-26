# Bus Alert Bot - Báo Cáo Dự Án

## 1. Tóm Tắt Dự Án

**Tên dự án**: Bus Alert Bot  
**Mục đích**: Phát triển một ứng dụng tự động cảnh báo thời gian đến của xe buýt qua Telegram  
**Công nghệ sử dụng**: Python 3, Telegram Bot API, Transport API  
**Trạng thái**: Hoàn thành và sẵn sàng triển khai  

---

## 2. Mô Tả Vấn Đề

Trong thực tế, người dùng phải thường xuyên kiểm tra lịch trình xe buýt trên nhiều ứng dụng khác nhau. Điều này gây mất thời gian và dễ bỏ lỡ chuyến xe. Dự án này giải quyết vấn đề bằng cách:

- Tự động kiểm tra thời gian xe buýt sắp đến
- Gửi thông báo theo thời gian thực qua Telegram
- Cung cấp thông tin chi tiết (số xe, điểm đến, thời gian đến)

---

## 3. Các Tính Năng Chính

### 3.1 Cảnh báo Đa Tầng
Bot gửi thông báo tại **3 mốc thời gian**:
- **15 phút** trước: Cảnh báo ban đầu
- **10 phút** trước: Cảnh báo thứ hai
- **5 phút** trước: Cảnh báo cuối cùng

### 3.2 Thông Tin Chi Tiết
Mỗi thông báo bao gồm:
```
🚌 Bus U2 → Destination
📍 The Barbican S-bound
⏱ Arriving in 15 min (14:30) (live)
```

### 3.3 Lọc Xe Buýc
- Có thể cấu hình để chỉ theo dõi các tuyến xe cụ thể (ví dụ: U2)
- Hoặc theo dõi tất cả các tuyến nếu cần

### 3.4 Dữ Liệu Thời Gian Thực
- Sử dụng `best_departure_estimate` từ API (nếu có)
- Dự phòng sử dụng `aimed_departure_time` (nếu không có dữ liệu thực tế)

### 3.5 Ngăn Chặn Thông Báo Trùng Lặp
- Theo dõi các chuyến xe đã cảnh báo
- Tự động xóa dữ liệu cũ để tránh lãng phí bộ nhớ

---

## 4. Kiến Trúc Kỹ Thuật

### 4.1 Cấu Trúc File
```
chatbot_bus/
├── bus_bot.py           # File chính của chương trình
├── requirements.txt     # Thư viện cần thiết
└── REPORT.md           # Báo cáo này
```

### 4.2 Thành Phần Chính

#### 4.2.1 Hàm `send_telegram(message)`
- Gửi tin nhắn đến Telegram Chat
- **Input**: Nội dung tin nhắn (HTML format)
- **Output**: Tin nhắn Telegram

#### 4.2.2 Hàm `get_departures()`
- Kết nối với Transport API để lấy dữ liệu xe buýt
- **Input**: ATCO_CODE (mã dừng xe)
- **Output**: Danh sách các chuyến xe sắp tới
- **API endpoint**: `https://transportapi.com/v3/uk/bus/stop/{ATCO_CODE}/live.json`

#### 4.2.3 Hàm `minutes_until(time_str)`
- Tính toán thời gian còn lại từ giờ hiện tại đến giờ xe đến
- **Input**: Chuỗi thời gian định dạng "HH:MM"
- **Output**: Số phút còn lại (int) hoặc None nếu không hợp lệ

#### 4.2.4 Hàm `check_buses()`
- Hàm chính để kiểm tra xe buýt sắp đến
- Lọc theo tuyến xe nếu cấu hình
- Gửi cảnh báo nếu thời gian <= ngưỡng
- Xóa dữ liệu cũ để giải phóng bộ nhớ

#### 4.2.5 Hàm `main()`
- Khởi động bot
- Lập lịch chạy `check_buses()` mỗi `CHECK_INTERVAL` phút
- Chạy vòng lặp vô hạn

### 4.3 Quy Trình Hoạt Động

```
┌─────────────────────────────────┐
│  Khởi động Bot                  │
│  - Gửi thông báo khởi động      │
│  - Setup lịch trình             │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Chạy mỗi CHECK_INTERVAL phút   │
│  - Lấy danh sách xe sắp tới     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Kiểm tra từng xe               │
│  - Lọc theo tuyến cấu hình      │
│  - Tính thời gian còn lại       │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  So sánh với ngưỡng cảnh báo    │
│  - Nếu <= 15, 10, 5 phút        │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Gửi thông báo Telegram         │
│  - Thêm vào danh sách đã báo    │
│  - Xóa dữ liệu cũ              │
└─────────────────────────────────┘
```

---

## 5. Cấu Hình

### 5.1 Biến Cơ Bản
| Biến | Giá Trị | Mô Tả |
|------|--------|-------|
| `TELEGRAM_TOKEN` | (API Token) | Token của Telegram Bot |
| `CHAT_ID` | (Chat ID) | ID nhóm/người dùng Telegram nhận cảnh báo |
| `ATCO_CODE` | 3290YYA00174 | Mã dừng xe buýt |
| `BUS_STOP_NAME` | The Barbican S-bound | Tên dừng xe |
| `ALERT_MINUTES` | [15,14,13,...,5,...,1] | Các mốc thời gian cảnh báo |
| `BUS_NUMBERS` | ["U2"] | Tuyến xe cần theo dõi |
| `CHECK_INTERVAL` | 2 | Kiểm tra mỗi 2 phút |

### 5.2 API Keys
- **Transport API**: app_id (`a5856328`) và app_key (`86b23613d64238bc895f4e0dba5e38b5`)

---

## 6. Yêu Cầu Hệ Thống

### 6.1 Thư Viện Python
```
requests==2.31.0      # HTTP requests để lấy dữ liệu API
schedule==1.2.0       # Lập lịch chạy periodic tasks
```

### 6.2 Yêu Cầu Khác
- Python 3.7+
- Kết nối Internet
- Tài khoản Telegram Bot

---

## 7. Cách Sử Dụng

### 7.1 Cài Đặt Cục Bộ
```bash
# Cài đặt thư viện
pip install -r requirements.txt

# Chạy bot
python bus_bot.py
```

### 7.2 Cấu Hình
1. Mở file `bus_bot.py`
2. Chỉnh sửa các biến trong phần CONFIG:
   - `ATCO_CODE`: Mã dừng xe của bạn
   - `BUS_STOP_NAME`: Tên dừng xe
   - `BUS_NUMBERS`: Tuyến xe muốn theo dõi
   - `ALERT_MINUTES`: Các mốc cảnh báo

### 7.3 Triển Khai 24/7 trên Render
1. Đẩy code lên GitHub
2. Vào https://render.com
3. Tạo Web Service mới
4. Kết nối GitHub repo
5. Điền Start Command: `python bus_bot.py`
6. Deploy!

---

## 8. Kết Quả & Kiểm Thử

### 8.1 Test trên Máy Cục Bộ
- ✅ Bot khởi động thành công
- ✅ Kết nối API Transport thành công
- ✅ Lấy dữ liệu xe buýt thành công
- ✅ Gửi thông báo Telegram thành công
- ✅ Các mốc cảnh báo hoạt động đúng

### 8.2 Ví Dụ Thông Báo
```
📲 Thông báo ban đầu (15 phút):
🚌 Bus U2 → City Centre
📍 The Barbican S-bound
⏱ Arriving in 15 min (14:30) (live)

📲 Cảnh báo thứ hai (10 phút):
🚌 Bus U2 → City Centre
📍 The Barbican S-bound
⏱ Arriving in 10 min (14:35) (live)

📲 Cảnh báo cuối (5 phút):
🚌 Bus U2 → City Centre
📍 The Barbican S-bound
⏱ Arriving in 5 min (14:40) (live)
```

---

## 9. Ưu & Nhược Điểm

### 9.1 Ưu Điểm
✅ Tiết kiệm thời gian kiểm tra xe buýt  
✅ Thông báo theo thời gian thực  
✅ Có thể tùy chỉnh dễ dàng  
✅ Chạy 24/7 trên cloud  
✅ Miễn phí (Render free tier)  
✅ Giao diện thân thiện qua Telegram  

### 9.2 Nhược Điểm
❌ Phụ thuộc vào API Transport (nếu down thì ko hoạt động)  
❌ Chỉ áp dụng cho xe buýt UK  
❌ Cần Internet liên tục  
❌ Render free tier có thể ngủ sau 15 phút không hoạt động  

---

## 10. Kết Luận

Bot Bus Alert Bot là một ứng dụng hữu ích giúp người dùng:
- Không bỏ lỡ chuyến xe buýc
- Quản lý thời gian hiệu quả
- Nhận thông báo (real-time) tự động

Dự án này minh chứng khả năng:
- Làm việc với API bên ngoài
- Xử lý dữ liệu thời gian thực
- Lập lịch tác vụ tự động
- Tích hợp Telegram Bot
- Triển khai ứng dụng cloud

Dự án đã sẵn sàng để triển khai trên môi trường production!

---

## 11. Tài Liệu Tham Khảo

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Transport API UK](https://www.transportapi.com/)
- [Python Schedule Library](https://schedule.readthedocs.io/)
- [Render Documentation](https://render.com/docs)

---

**Sinh viên**: Kevin Ha  
**Ngày hoàn thành**: 26/03/2026  
**Trạng thái**: Hoàn thành ✅
