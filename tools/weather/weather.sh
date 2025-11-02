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
# Normalize Vietnamese text (remove diacritics AND spaces) for better API matching
if command -v python3 &> /dev/null; then
    normalized_location=$(echo "$LOCATION" | python3 -c "
import sys, unicodedata
text = sys.stdin.read().strip()
# Normalize to NFD (decompose) then remove combining characters
normalized = unicodedata.normalize('NFD', text)
ascii_text = ''.join(char for char in normalized if not unicodedata.combining(char))
# Remove spaces for better matching: 'Ha Noi' -> 'Hanoi', 'New York' -> 'NewYork'
ascii_text = ascii_text.replace(' ', '')
print(ascii_text)
")
else
    # Fallback: basic Vietnamese character replacement and remove spaces
    normalized_location=$(echo "$LOCATION" | sed -e 's/à\|á\|ạ\|ả\|ã\|â\|ầ\|ấ\|ậ\|ẩ\|ẫ\|ă\|ằ\|ắ\|ặ\|ẳ\|ẵ/a/g' \
        -e 's/è\|é\|ẹ\|ẻ\|ẽ\|ê\|ề\|ế\|ệ\|ể\|ễ/e/g' \
        -e 's/ì\|í\|ị\|ỉ\|ĩ/i/g' \
        -e 's/ò\|ó\|ọ\|ỏ\|õ\|ô\|ồ\|ố\|ộ\|ổ\|ỗ\|ơ\|ờ\|ớ\|ợ\|ở\|ỡ/o/g' \
        -e 's/ù\|ú\|ụ\|ủ\|ũ\|ư\|ừ\|ứ\|ự\|ử\|ữ/u/g' \
        -e 's/ỳ\|ý\|ỵ\|ỷ\|ỹ/y/g' \
        -e 's/đ/d/g' \
        -e 's/À\|Á\|Ạ\|Ả\|Ã\|Â\|Ầ\|Ấ\|Ậ\|Ẩ\|Ẫ\|Ă\|Ằ\|Ắ\|Ặ\|Ẳ\|Ẵ/A/g' \
        -e 's/È\|É\|Ẹ\|Ẻ\|Ẽ\|Ê\|Ề\|Ế\|Ệ\|Ể\|Ễ/E/g' \
        -e 's/Ì\|Í\|Ị\|Ỉ\|Ĩ/I/g' \
        -e 's/Ò\|Ó\|Ọ\|Ỏ\|Õ\|Ô\|Ồ\|Ố\|Ộ\|Ổ\|Ỗ\|Ơ\|Ờ\|Ớ\|Ợ\|Ở\|Ỡ/O/g' \
        -e 's/Ù\|Ú\|Ụ\|Ủ\|Ũ\|Ư\|Ừ\|Ứ\|Ự\|Ử\|Ữ/U/g' \
        -e 's/Ỳ\|Ý\|Ỵ\|Ỷ\|Ỹ/Y/g' \
        -e 's/Đ/D/g' \
        -e 's/ //g')
fi

# Get multiple results to find the best match (prioritize capitals and major cities)
# No need to encode since normalized_location has no spaces
geocode_response=$(curl -s "https://geocoding-api.open-meteo.com/v1/search?name=${normalized_location}&count=5&language=en")

# Parse latitude và longitude
if command -v python3 &> /dev/null; then
    coordinates=$(echo "$geocode_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'results' in data and len(data['results']) > 0:
        # Prioritize results by population first, then feature code
        # This ensures big cities like NYC (8M pop) win over small towns
        def score_result(r):
            population = r.get('population', 0)
            feature_code = r.get('feature_code', '')
            
            # Bonus for capitals and major cities
            feature_bonus = 0
            if feature_code == 'PPLC':  # Capital
                feature_bonus = 10000000
            elif feature_code == 'PPLA':  # Admin level 1
                feature_bonus = 1000000
            elif feature_code == 'PPLA2':  # Admin level 2
                feature_bonus = 100000
            
            # Total score = population + bonus
            # This way NYC (8.8M) beats York, NE (7K + 100K bonus)
            return population + feature_bonus
        
        # Sort by score (descending)
        sorted_results = sorted(data['results'], key=score_result, reverse=True)
        result = sorted_results[0]
        
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
