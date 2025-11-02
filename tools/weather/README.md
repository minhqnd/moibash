# Weather Tool - Công cụ xem thời tiết

Công cụ lấy thông tin thời tiết sử dụng **Gemini Function Calling** và **Open-Meteo API**.

## 📁 Cấu trúc

```
tools/weather/
├── function_call.sh    # File chính - Xử lý Function Calling với Gemini
├── weather.sh          # File phụ - Lấy dữ liệu từ Open-Meteo API
└── README.md          # File này
```

## 🚀 Cách hoạt động

### Flow hoạt động (CẢI TIẾN MỚI):

1. **User input** → "Thời tiết ở Hà Nội thế nào?"
2. **Gemini Function Calling** → 
   - Extract location: `"Hà Nội"`
   - **TỰ ĐỘNG chuẩn hóa**: Bỏ dấu tiếng Việt → `"Ha Noi"`
   - Giữ nguyên khoảng trắng để API nhận diện tốt hơn
3. **Geocoding API** → 
   - Chuyển đổi "Ha Noi" → tìm nhiều kết quả
   - **Ưu tiên** thủ đô/thành phố lớn (PPLC > PPLA > PPL)
   - Chọn kết quả có dân số cao nhất → Hanoi (21.0245, 105.84117)
4. **Weather API** → Lấy thông tin thời tiết từ tọa độ
5. **Gemini với System Instruction** → Tạo phân tích ĐẦY ĐỦ:
   - 📍 Vị trí & tọa độ
   - 🌡️ Nhiệt độ
   - 💧 Lượng mưa
   - 💬 Nhận xét chi tiết (đánh giá nhiệt độ, gợi ý trang phục, lời khuyên hoạt động)

### Sơ đồ:

```
┌─────────────────┐
│  User Message   │
│ "Thời tiết HN?" │
└────────┬────────┘
         │
         v
┌─────────────────────────┐
│  function_call.sh       │
│  Gemini Function Call   │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│  Extract: "Hà Nội"      │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│     weather.sh          │
├─────────────────────────┤
│ 1. Geocoding API        │
│    HN → (21.0, 105.8)   │
│                         │
│ 2. Weather API          │
│    → Temperature, Rain  │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│  JSON Response          │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│  Format & Display       │
│  🌤️ Thời tiết tại HN   │
│  🌡️ Nhiệt độ: 25°C     │
└─────────────────────────┘
```

## 📝 Sử dụng

### 1. Test trực tiếp file weather.sh

```bash
# Lấy thông tin thời tiết cho một địa điểm
./tools/weather/weather.sh "Ha Noi"
./tools/weather/weather.sh "London"
./tools/weather/weather.sh "Tokyo"
```

**Output mẫu:**
```json
{
  "location": "Hà Nội",
  "country": "Vietnam",
  "latitude": 21.0285,
  "longitude": 105.8542,
  "temperature": 25.5,
  "rain": 0.0,
  "time": "2025-11-02T19:30",
  "unit": "°C"
}
```

### 2. Test function_call.sh (với Gemini)

```bash
# Hỏi về thời tiết bằng ngôn ngữ tự nhiên
./tools/weather/function_call.sh "Thời tiết ở Hà Nội hôm nay thế nào?"
./tools/weather/function_call.sh "Nhiệt độ ở Tokyo bao nhiêu?"
./tools/weather/function_call.sh "What's the weather in London?"
```

**Output mẫu:**
```
🌤️ Thông tin thời tiết tại Hà Nội, Vietnam

🌡️ Nhiệt độ: 25.5°C
☔ Lượng mưa: 0.0 mm
🕐 Thời gian: 2025-11-02T19:30
📍 Tọa độ: 21.0285, 105.8542

💬 Phân tích:
Hiện tại ở Hà Nội trời khá mát mẻ với nhiệt độ khoảng 25.5°C, 
không có mưa. Thời tiết phù hợp để đi dạo hoặc hoạt động ngoài trời.
```

### 3. Sử dụng qua Router (main.sh)

```bash
# Agent tự động phát hiện intent là "weather"
./router.sh "Thời tiết ở Hà Nội thế nào?"
./router.sh "Hôm nay Tokyo có mưa không?"
```

## 🔧 API được sử dụng

### 1. Gemini Function Calling API
- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`
- **Mục đích:** Extract location từ câu hỏi tự nhiên
- **Function:** `get_current_weather(location: string)`

### 2. Geocoding API (Open-Meteo)
- **Endpoint:** `https://geocoding-api.open-meteo.com/v1/search`
- **Mục đích:** Chuyển đổi tên địa điểm → tọa độ (latitude, longitude)
- **Parameters:**
  - `name`: Tên địa điểm (ví dụ: "Ha Noi", "London")
  - `count`: Số kết quả trả về (mặc định: 1)
  - `language`: Ngôn ngữ (mặc định: "en")

### 3. Weather Forecast API (Open-Meteo)
- **Endpoint:** `https://api.open-meteo.com/v1/forecast`
- **Mục đích:** Lấy thông tin thời tiết theo tọa độ
- **Parameters:**
  - `latitude`, `longitude`: Tọa độ
  - `current`: Thông tin hiện tại (temperature_2m, rain)
  - `hourly`: Dự báo theo giờ
  - `timezone`: Múi giờ (mặc định: Asia/Bangkok)
  - `forecast_days`: Số ngày dự báo (mặc định: 1)

## 🧪 Testing các API

### Test Geocoding API:
```bash
curl -s "https://geocoding-api.open-meteo.com/v1/search?name=Ha+noi&count=1&language=en" | python3 -m json.tool
```

### Test Weather API:
```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=21.0285&longitude=105.8542&hourly=temperature_2m,rain&current=temperature_2m,rain&timezone=Asia%2FBangkok&forecast_days=1" | python3 -m json.tool
```

### Test Function Calling:
```bash
source .env
curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$GEMINI_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{"role": "user", "parts": [{"text": "Thời tiết ở Tokyo?"}]}],
    "tools": [{
      "functionDeclarations": [{
        "name": "get_current_weather",
        "description": "Lấy thông tin thời tiết",
        "parameters": {
          "type": "object",
          "properties": {"location": {"type": "string"}},
          "required": ["location"]
        }
      }]
    }]
  }' | python3 -m json.tool
```

## 🎯 Tính năng nổi bật

### 1. ✨ Gemini tự động chuẩn hóa tên địa điểm
Không cần code xử lý phức tạp - Gemini làm tất cả:
- `"Hà Nội"` → `"Ha Noi"` (bỏ dấu)
- `"Đà Nẵng"` → `"Da Nang"`
- `"Hồ Chí Minh"` → `"Ho Chi Minh"`
- Giữ nguyên khoảng trắng để Geocoding API hoạt động tốt

**Cách thực hiện:** Hướng dẫn Gemini trong `description` của function parameter:
```json
{
  "location": {
    "type": "string",
    "description": "Tên địa điểm cần tra cứu thời tiết. QUAN TRỌNG: Chỉ bỏ dấu tiếng Việt, KHÔNG bỏ khoảng trắng..."
  }
}
```

### 2. 🎯 Smart location matching
- Lấy 5 kết quả từ Geocoding API
- Ưu tiên theo:
  - `PPLC` (capital) > `PPLA` (admin) > `PPL` (populated)
  - Dân số cao hơn
- Đảm bảo chọn đúng thủ đô Hanoi thay vì thị trấn Hà Nội ở Hà Nam

### 3. 💬 Response đầy đủ với System Instruction
Gemini tự động tạo phân tích thời tiết đầy đủ:
- Đánh giá nhiệt độ (nóng/mát/lạnh)
- Tình trạng mưa
- Gợi ý trang phục
- Lời khuyên hoạt động ngoài trời

## 📋 Requirements

- **bash** (zsh hoặc bash)
- **curl** (gọi API)
- **python3** (parse JSON - optional, có fallback)
- **GEMINI_API_KEY** trong file `.env`

## ⚙️ Cấu hình

File `.env` cần có:
```bash
GEMINI_API_KEY='your-gemini-api-key-here'
```

## 🐛 Xử lý lỗi

### 1. Không tìm thấy địa điểm
```
❌ Không tìm thấy địa điểm: XYZ
```
→ Kiểm tra tên địa điểm, thử với tên khác

### 2. API Key hết quota
```
❌ You exceeded your current quota
```
→ Đợi quota reset hoặc nâng cấp plan

### 3. Không extract được location
```
❌ Không thể xác định địa điểm từ câu hỏi của bạn.
💡 Vui lòng đặt câu hỏi rõ ràng hơn
```
→ Đặt câu hỏi rõ ràng hơn với tên địa điểm cụ thể

## 📚 Tài liệu tham khảo

- [Gemini Function Calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Open-Meteo API Documentation](https://open-meteo.com/en/docs)
- [Geocoding API](https://open-meteo.com/en/docs/geocoding-api)

## 🎯 Ví dụ câu hỏi

✅ **Câu hỏi tốt:**
- "Thời tiết ở Hà Nội hôm nay thế nào?"
- "Nhiệt độ ở Tokyo bao nhiêu độ?"
- "What's the temperature in London?"
- "Hôm nay Paris có mưa không?"

❌ **Câu hỏi không rõ:**
- "Hôm nay thế nào?" (thiếu địa điểm)
- "Thời tiết nè" (không có địa điểm)
- "Mưa không?" (không biết ở đâu)

## 🔄 Tích hợp với Intent Classification

File `intent.sh` đã được cập nhật để nhận diện intent `weather`:

```bash
# 4 intents được hỗ trợ:
- chat          # Trò chuyện thông thường
- image_create  # Tạo ảnh
- google_search # Tìm kiếm
- weather       # Thời tiết (MỚI!)
```

File `router.sh` tự động route đến `weather/function_call.sh` khi phát hiện intent weather.

## 💡 Ghi chú

- **Geocoding API** hỗ trợ cả tiếng Việt và tiếng Anh
- **Weather API** miễn phí, không cần API key
- **Function Calling** cần GEMINI_API_KEY
- Dữ liệu thời tiết cập nhật theo thời gian thực
- Hỗ trợ dự báo 1 ngày (có thể mở rộng)
