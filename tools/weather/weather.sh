#!/bin/bash

# weather.sh - Lấy thông tin thời tiết từ Open-Meteo API
# Input: location name
# Output: thông tin thời tiết

LOCATION="$1"

if [ -z "$LOCATION" ]; then
    echo "❌ Lỗi: Vui lòng cung cấp tên địa điểm!"
    exit 1
fi

# Bước 1: Chuyển đổi tên địa điểm sang tọa độ
# Encode location name cho URL
encoded_location=$(echo "$LOCATION" | sed 's/ /+/g')

geocode_response=$(curl -s "https://geocoding-api.open-meteo.com/v1/search?name=${encoded_location}&count=1&language=en")

# Parse latitude và longitude
if command -v python3 &> /dev/null; then
    coordinates=$(echo "$geocode_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'results' in data and len(data['results']) > 0:
        result = data['results'][0]
        print(f\"{result['latitude']}|{result['longitude']}|{result['name']}|{result.get('country', '')}\")
    else:
        print('NOT_FOUND')
except:
    print('ERROR')
" 2>/dev/null)
else
    # Fallback nếu không có python
    latitude=$(echo "$geocode_response" | grep -o '"latitude"[[:space:]]*:[[:space:]]*[0-9.-]*' | head -1 | grep -o '[0-9.-]*$')
    longitude=$(echo "$geocode_response" | grep -o '"longitude"[[:space:]]*:[[:space:]]*[0-9.-]*' | head -1 | grep -o '[0-9.-]*$')
    
    if [ -z "$latitude" ] || [ -z "$longitude" ]; then
        coordinates="NOT_FOUND"
    else
        coordinates="${latitude}|${longitude}|${LOCATION}|"
    fi
fi

# Kiểm tra kết quả geocoding
if [ "$coordinates" == "NOT_FOUND" ]; then
    echo "{\"error\": \"Không tìm thấy địa điểm: $LOCATION\"}"
    exit 1
elif [ "$coordinates" == "ERROR" ]; then
    echo "{\"error\": \"Lỗi khi xử lý dữ liệu geocoding\"}"
    exit 1
fi

# Tách thông tin
IFS='|' read -r latitude longitude location_name country <<< "$coordinates"

# Bước 2: Lấy thông tin thời tiết
weather_response=$(curl -s "https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&hourly=temperature_2m,rain&current=temperature_2m,rain&timezone=Asia%2FBangkok&forecast_days=1")

# Parse thông tin thời tiết
if command -v python3 &> /dev/null; then
    weather_info=$(echo "$weather_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    current = data.get('current', {})
    
    # Lấy thông tin hiện tại
    temp = current.get('temperature_2m', 'N/A')
    rain = current.get('rain', 0)
    time = current.get('time', 'N/A')
    
    # Format output JSON
    result = {
        'location': '$location_name',
        'country': '$country',
        'latitude': $latitude,
        'longitude': $longitude,
        'temperature': temp,
        'rain': rain,
        'time': time,
        'unit': '°C'
    }
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'error': f'Lỗi parse dữ liệu: {str(e)}'}))
" 2>/dev/null)
else
    # Fallback parsing
    temp=$(echo "$weather_response" | grep -o '"temperature_2m"[[:space:]]*:[[:space:]]*[0-9.-]*' | head -1 | grep -o '[0-9.-]*$')
    rain=$(echo "$weather_response" | grep -o '"rain"[[:space:]]*:[[:space:]]*[0-9.-]*' | head -1 | grep -o '[0-9.-]*$')
    
    weather_info="{\"location\": \"$location_name\", \"country\": \"$country\", \"temperature\": $temp, \"rain\": $rain, \"unit\": \"°C\"}"
fi

echo "$weather_info"
