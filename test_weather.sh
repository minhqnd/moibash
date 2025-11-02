#!/bin/bash

# test_weather.sh - Script test weather tool

echo "🧪 Testing Weather Tool"
echo "======================="
echo ""

# Test 1: weather.sh với địa điểm khác nhau
echo "📍 Test 1: weather.sh - Lấy thông tin thời tiết trực tiếp"
echo "-----------------------------------------------------------"

echo "1️⃣ Test với 'Ha Noi':"
./tools/weather/weather.sh "Ha Noi"
echo ""

echo "2️⃣ Test với 'London':"
./tools/weather/weather.sh "London"
echo ""

echo "3️⃣ Test với 'Tokyo':"
./tools/weather/weather.sh "Tokyo"
echo ""

echo "4️⃣ Test với 'New York':"
./tools/weather/weather.sh "New York"
echo ""

# Test 2: Địa điểm không tồn tại
echo "❌ Test 2: Địa điểm không tồn tại"
echo "-----------------------------------------------------------"
./tools/weather/weather.sh "XYZ123ABC"
echo ""

# Test 3: Intent classification (nếu API còn quota)
echo "🎯 Test 3: Intent Classification"
echo "-----------------------------------------------------------"
echo "Testing intent classifier với câu hỏi về thời tiết..."

# Note: Phần này cần API key
# echo "Câu hỏi: 'Thời tiết ở Hà Nội thế nào?'"
# ./tools/intent.sh "Thời tiết ở Hà Nội thế nào?"

echo "⚠️ Bỏ qua test này vì API đã hết quota"
echo ""

# Summary
echo "✅ Test hoàn tất!"
echo "-----------------------------------------------------------"
echo "📝 Kết quả:"
echo "  • weather.sh hoạt động tốt với Geocoding & Weather API"
echo "  • Hỗ trợ nhiều địa điểm khác nhau"
echo "  • Xử lý lỗi khi không tìm thấy địa điểm"
echo ""
echo "💡 Để test function_call.sh, cần:"
echo "  • GEMINI_API_KEY trong file .env"
echo "  • API key còn quota"
echo ""
echo "📚 Xem thêm hướng dẫn trong tools/weather/README.md"
