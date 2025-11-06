#!/bin/bash

# music.sh - Lấy thông tin bài hát từ iTunes API
# Input: tên bài hát
# Output: thông tin + phát preview (nếu có)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
QUERY="$*"
if [ -z "$QUERY" ]; then
  echo "❌ Lỗi: Vui lòng nhập tên bài hát!"
  exit 1
fi

encoded_query=$(echo "$QUERY" | sed 's/ /+/g')
response=$(curl -s "https://itunes.apple.com/search?term=${encoded_query}&entity=song&limit=1")

music_info=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if not data['results']:
        print(json.dumps({'error': 'Không tìm thấy bài hát!'}, ensure_ascii=False))
        sys.exit(1)
    song = data['results'][0]
    info = {
        'track': song.get('trackName', 'N/A'),
        'artist': song.get('artistName', 'N/A'),
        'album': song.get('collectionName', 'N/A'),
        'genre': song.get('primaryGenreName', 'N/A'),
        'release_date': song.get('releaseDate', 'N/A')[:10],
        'preview_url': song.get('previewUrl', ''),
        'itunes_link': song.get('trackViewUrl', '')
    }
    print(json.dumps(info, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'error': str(e)}, ensure_ascii=False))
")

# Parse JSON kết quả
track=$(echo "$music_info" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('track',''))")
artist=$(echo "$music_info" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('artist',''))")
album=$(echo "$music_info" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('album',''))")
genre=$(echo "$music_info" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('genre',''))")
release_date=$(echo "$music_info" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('release_date',''))")
itunes_link=$(echo "$music_info" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('itunes_link',''))")
preview_url=$(echo "$music_info" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('preview_url',''))")

if echo "$music_info" | grep -q '"error"'; then
  echo "$music_info"
  exit 1
fi

echo "🎧 Bài hát: $track"
echo "👤 Ca sĩ: $artist"
echo "💿 Album: $album"
echo "🎭 Thể loại: $genre"
echo "📅 Phát hành: $release_date"
echo "🔗 iTunes: $itunes_link"

# Phát preview nếu có
if [ -n "$preview_url" ]; then
  "$SCRIPT_DIR/play.sh" "$preview_url"
else
  echo "ℹ️ Không có bản preview cho bài hát này."
fi