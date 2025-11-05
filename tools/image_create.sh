#!/bin/bash

# image_create.sh - Tạo ảnh với Gemini Image Generation

# Load .env
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f "$SCRIPT_DIR/../.env" ]; then
    set -a
    source "$SCRIPT_DIR/../.env"
    set +a
fi

USER_MESSAGE="$1"

if [ -z "$USER_MESSAGE" ]; then
    echo "❌ Không có mô tả ảnh"
    exit 1
fi

# Tạo thư mục images
IMAGES_DIR="$SCRIPT_DIR/../images"
mkdir -p "$IMAGES_DIR"

# Tên file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
IMAGE_FILE="$IMAGES_DIR/image_$TIMESTAMP.png"

echo "🎨 Đang tạo ảnh..."

# Gọi API và save ảnh
curl -s -X POST \
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent?key=$GEMINI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"contents\": [{
        \"parts\": [{\"text\": \"$USER_MESSAGE\"}]
      }],
      \"generationConfig\": {
        \"responseModalities\": [\"IMAGE\", \"TEXT\"]
      }
    }" \
    | grep -o '"data": "[^"]*"' \
    | cut -d'"' -f4 \
    | base64 --decode > "$IMAGE_FILE"

# Kiểm tra
if [ -s "$IMAGE_FILE" ]; then
    echo "✅ Đã tạo ảnh: $IMAGE_FILE"
    
    # Mở ảnh
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$IMAGE_FILE"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$IMAGE_FILE" 2>/dev/null
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        start "$IMAGE_FILE" 2>/dev/null || cmd.exe /c start "$IMAGE_FILE"
    fi
    
    exit 0
else
    echo "❌ Không thể tạo ảnh"
    rm -f "$IMAGE_FILE"
    exit 1
fi
