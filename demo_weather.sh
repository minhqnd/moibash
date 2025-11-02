#!/bin/bash

# demo_weather.sh - Demo script cho Weather Intent

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RESET='\033[0m'
BOLD='\033[1m'

# Hàm hiển thị header
show_header() {
    clear
    echo -e "${CYAN}${BOLD}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         🌤️  WEATHER INTENT DEMONSTRATION 🌤️               ║"
    echo "║                                                            ║"
    echo "║  Tính năng: Lấy thông tin thời tiết với Function Calling  ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"
    echo ""
}

# Hàm delay
delay() {
    sleep 1
}

# Main demo
show_header

echo -e "${YELLOW}${BOLD}📁 BƯỚC 1: Cấu trúc thư mục${RESET}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo "tools/"
echo "└── weather/"
echo "    ├── function_call.sh  (Gemini Function Calling)"
echo "    ├── weather.sh        (Weather API)"
echo "    └── README.md         (Documentation)"
echo ""
delay

echo -e "${YELLOW}${BOLD}🌐 BƯỚC 2: Test Geocoding API${RESET}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "${GREEN}$ curl \"https://geocoding-api.open-meteo.com/v1/search?name=Ha+noi&count=1\"${RESET}"
echo ""
curl -s "https://geocoding-api.open-meteo.com/v1/search?name=Ha+noi&count=1&language=en" | python3 -c "
import sys, json
data = json.load(sys.stdin)
result = data['results'][0]
print(f\"📍 Location: {result['name']}, {result['country']}\")
print(f\"📌 Coordinates: ({result['latitude']}, {result['longitude']})\")"
echo ""
delay

echo -e "${YELLOW}${BOLD}🌤️ BƯỚC 3: Test Weather API${RESET}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "${GREEN}$ ./tools/weather/weather.sh \"Ha Noi\"${RESET}"
echo ""
./tools/weather/weather.sh "Ha Noi" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"🌤️ Thông tin thời tiết tại {data['location']}, {data['country']}\")
print(f\"🌡️  Nhiệt độ: {data['temperature']}°C\")
print(f\"☔ Lượng mưa: {data['rain']} mm\")
print(f\"🕐 Thời gian: {data['time']}\")"
echo ""
delay

echo -e "${YELLOW}${BOLD}🌍 BƯỚC 4: Test với nhiều địa điểm${RESET}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

locations=("London" "Tokyo" "New York" "Paris")

for loc in "${locations[@]}"; do
    echo -e "${GREEN}📍 $loc:${RESET}"
    ./tools/weather/weather.sh "$loc" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"   🌡️  {data['temperature']}°C | ☔ {data['rain']}mm\")"
    delay
done
echo ""

echo -e "${YELLOW}${BOLD}🎯 BƯỚC 5: Intent Classification${RESET}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo "4 Intents được hỗ trợ:"
echo "  1. chat          - Trò chuyện thông thường"
echo "  2. image_create  - Tạo ảnh"
echo "  3. google_search - Tìm kiếm"
echo "  4. weather       - Thời tiết (MỚI!)"
echo ""
delay

echo -e "${YELLOW}${BOLD}🚀 BƯỚC 6: Integration với Router${RESET}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo "Flow hoàn chỉnh:"
echo ""
echo "  User Input"
echo "      ↓"
echo "  router.sh"
echo "      ↓"
echo "  intent.sh (classify: weather)"
echo "      ↓"
echo "  weather/function_call.sh"
echo "      ↓"
echo "  weather/weather.sh"
echo "      ↓"
echo "  Display Result"
echo ""
delay

echo -e "${YELLOW}${BOLD}✨ BƯỚC 7: Gemini Function Calling${RESET}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo "Function Declaration:"
echo ""
cat << 'EOF'
{
  "name": "get_current_weather",
  "description": "Lấy thông tin thời tiết hiện tại...",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "Tên địa điểm"
      }
    },
    "required": ["location"]
  }
}
EOF
echo ""
echo "⚠️  Note: Cần GEMINI_API_KEY để sử dụng function calling"
echo ""
delay

echo -e "${YELLOW}${BOLD}📊 BƯỚC 8: Kết quả${RESET}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo "✅ Hoàn thành:"
echo "   • Tạo weather intent"
echo "   • Tích hợp Gemini Function Calling"
echo "   • Sử dụng Open-Meteo API (Geocoding + Weather)"
echo "   • Xử lý lỗi đầy đủ"
echo "   • Documentation chi tiết"
echo ""
echo "📚 Xem thêm:"
echo "   • tools/weather/README.md - Hướng dẫn chi tiết"
echo "   • WEATHER_IMPLEMENTATION.md - Tóm tắt implementation"
echo ""

echo -e "${CYAN}${BOLD}╔════════════════════════════════════════════════════════════╗"
echo -e "║              ✨ DEMO HOÀN THÀNH! ✨                        ║"
echo -e "╚════════════════════════════════════════════════════════════╝${RESET}"
echo ""
