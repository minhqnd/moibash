#!/bin/bash
# function_call.sh - Điểm vào (entry point) của Music Agent
# Nhận input từ chatbot, gọi tới music.sh để xử lý

USER_INPUT="$1"

# --- Kiểm tra input ---
if [ -z "$USER_INPUT" ]; then
    echo "❌ Lỗi: Không có câu lệnh đầu vào!"
    echo "Ví dụ: bash tools/music/function_call.sh 'phát bài Shape of You'"
    exit 1
fi

# --- In log nhỏ cho debug ---
echo "🎧 Music Agent nhận yêu cầu: $USER_INPUT"

# --- Gọi file xử lý chính ---
bash tools/music/music.sh "$USER_INPUT"
status=$?

# --- Kiểm tra kết quả ---
if [ $status -ne 0 ]; then
    echo "⚠️ Có lỗi xảy ra trong quá trình xử lý yêu cầu âm nhạc."
else
    echo "✅ Music Agent hoàn tất yêu cầu."
fi