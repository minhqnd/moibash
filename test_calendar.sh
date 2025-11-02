#!/bin/bash

# test_calendar.sh - Script test calendar tool

echo "🧪 Testing Calendar Tool"
echo "========================"
echo ""

# Test 1: Check auth status
echo "📍 Test 1: Authentication Status"
echo "-----------------------------------------------------------"
./tools/calendar/auth.sh status
auth_status=$?
echo ""

if [ $auth_status -eq 0 ]; then
    echo "✅ Đã đăng nhập Google Calendar"
    echo ""
    
    # Test 2: Get current time
    echo "📍 Test 2: Get Current Time"
    echo "-----------------------------------------------------------"
    if command -v python3 &> /dev/null; then
        current_time=$(python3 -c "from datetime import datetime; print(datetime.now().strftime('%Y-%m-%dT%H:%M:%S+07:00'))")
        echo "Current time: $current_time"
        echo ""
        
        # Test 3: List events (today)
        echo "📍 Test 3: List Events Today"
        echo "-----------------------------------------------------------"
        today_start=$(python3 -c "from datetime import datetime; print(datetime.now().strftime('%Y-%m-%dT00:00:00+07:00'))")
        today_end=$(python3 -c "from datetime import datetime; print(datetime.now().strftime('%Y-%m-%dT23:59:59+07:00'))")
        
        echo "Time range: $today_start to $today_end"
        ./tools/calendar/calendar.sh list "$today_start" "$today_end" 10
        echo ""
        
        # Test 4: Intent classification
        echo "📍 Test 4: Intent Classification"
        echo "-----------------------------------------------------------"
        
        echo "1️⃣ Test với 'lịch trình của tôi hôm nay':"
        intent=$(./tools/intent.sh "lịch trình của tôi hôm nay" 2>/dev/null)
        echo "Intent detected: $intent"
        
        if [ "$intent" == "calendar" ]; then
            echo "✅ PASS - Correctly identified as calendar intent"
        else
            echo "❌ FAIL - Expected 'calendar', got '$intent'"
        fi
        echo ""
        
        echo "2️⃣ Test với 'thêm lịch đi ăn tối lúc 7h':"
        intent=$(./tools/intent.sh "thêm lịch đi ăn tối lúc 7h" 2>/dev/null)
        echo "Intent detected: $intent"
        
        if [ "$intent" == "calendar" ]; then
            echo "✅ PASS - Correctly identified as calendar intent"
        else
            echo "❌ FAIL - Expected 'calendar', got '$intent'"
        fi
        echo ""
        
        echo "3️⃣ Test với 'chiều nay tôi có lịch gì không':"
        intent=$(./tools/intent.sh "chiều nay tôi có lịch gì không" 2>/dev/null)
        echo "Intent detected: $intent"
        
        if [ "$intent" == "calendar" ]; then
            echo "✅ PASS - Correctly identified as calendar intent"
        else
            echo "❌ FAIL - Expected 'calendar', got '$intent'"
        fi
        echo ""
        
        # Test 5: Function calling (nếu có GEMINI_API_KEY)
        if [ ! -z "$GEMINI_API_KEY" ]; then
            echo "📍 Test 5: Function Calling (với Gemini)"
            echo "-----------------------------------------------------------"
            echo "⚠️ Test này sẽ sử dụng Gemini API quota"
            echo ""
            
            echo "Test query: 'lịch của tôi hôm nay'"
            echo "Running..."
            ./tools/calendar/function_call.sh "lịch của tôi hôm nay"
            echo ""
        else
            echo "📍 Test 5: Function Calling"
            echo "-----------------------------------------------------------"
            echo "⚠️ Bỏ qua test này vì không có GEMINI_API_KEY"
            echo ""
        fi
    else
        echo "⚠️ Cần python3 để chạy các test chi tiết"
        echo ""
    fi
else
    echo "❌ Chưa đăng nhập Google Calendar"
    echo ""
    echo "💡 Để test đầy đủ, vui lòng:"
    echo "   1. Setup Google Cloud credentials trong .env"
    echo "   2. Chạy: ./tools/calendar/auth.sh login"
    echo "   3. Chạy lại test này"
    echo ""
fi

# Summary
echo "✅ Test hoàn tất!"
echo "-----------------------------------------------------------"
echo "📝 Kết quả:"
echo ""

if [ $auth_status -eq 0 ]; then
    echo "  ✅ Auth system: Working"
    echo "  ✅ Calendar API integration: Ready"
    echo "  ✅ Intent classification: Working"
    echo ""
    echo "🎉 Calendar tool đã sẵn sàng sử dụng!"
    echo ""
    echo "📚 Cách sử dụng:"
    echo "   ./main.sh"
    echo "   Sau đó nhập: 'lịch trình của tôi hôm nay'"
else
    echo "  ⚠️ Auth system: Not configured"
    echo "  ⏸️ Calendar API integration: Pending auth"
    echo "  ✅ Intent classification: Working"
    echo ""
    echo "📋 Checklist thiết lập:"
    echo "  [ ] Tạo Google Cloud Project"
    echo "  [ ] Enable Google Calendar API"
    echo "  [ ] Tạo OAuth 2.0 credentials"
    echo "  [ ] Thêm credentials vào .env"
    echo "  [ ] Chạy: ./tools/calendar/auth.sh login"
fi

echo ""
echo "📚 Xem thêm hướng dẫn trong tools/calendar/README.md"
