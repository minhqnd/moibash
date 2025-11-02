#!/bin/bash

# demo.sh - Demo nhanh chat agent với các câu hỏi mẫu
# Chạy: ./demo.sh

echo "🎬 DEMO CHAT AGENT - Gemini API"
echo "================================"
echo ""

# Kiểm tra .env
if [ ! -f ".env" ]; then
    echo "❌ Chưa có file .env! Vui lòng tạo file .env trước."
    echo "Chạy: cp .env.example .env"
    echo "Sau đó thêm API key vào file .env"
    exit 1
fi

# Các câu hỏi demo
questions=(
    "Xin chào! Bạn là ai?"
    "Giải thích ngắn gọn về process trong hệ điều hành"
    "Sự khác biệt giữa thread và process?"
    "Bash script có thể làm gì?"
)

echo "📝 Sẽ gửi ${#questions[@]} câu hỏi mẫu..."
echo ""

for i in "${!questions[@]}"; do
    question="${questions[$i]}"
    num=$((i + 1))
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❓ Câu hỏi $num: $question"
    echo ""
    echo "💬 Gemini AI:"
    
    # Gọi agent
    ./agent.sh "$question"
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Đợi 2 giây giữa các câu hỏi
    if [ $num -lt ${#questions[@]} ]; then
        sleep 2
    fi
done

echo "✅ Demo hoàn tất!"
echo ""
echo "Bây giờ bạn có thể chạy chat client: ./main.sh"
