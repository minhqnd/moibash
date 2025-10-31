#!/bin/bash

# agent.sh - Xử lý tin nhắn và trả về mock response
# Môn: Hệ Điều Hành

# Nhận tin nhắn từ tham số
USER_MESSAGE="$1"

# Chuyển tin nhắn thành chữ thường để dễ xử lý
LOWER_MESSAGE=$(echo "$USER_MESSAGE" | tr '[:upper:]' '[:lower:]')

# Mảng các response ngẫu nhiên chung
GENERAL_RESPONSES=(
    "Thật thú vị! Cho mình biết thêm về điều đó được không?"
    "Mình hiểu rồi! Còn gì khác bạn muốn chia sẻ không?"
    "Được đấy! Bạn có câu hỏi nào khác không?"
    "Nghe hay đấy! Mình đang lắng nghe bạn nè! 👂"
    "Ồ! Điều đó nghe rất cool! 😊"
    "Cảm ơn bạn đã chia sẻ! Mình rất quan tâm!"
    "Tuyệt vời! Bạn còn điều gì muốn nói không?"
)

# Hàm chọn response ngẫu nhiên từ mảng
get_random_response() {
    local responses=("$@")
    local count=${#responses[@]}
    local index=$((RANDOM % count))
    echo "${responses[$index]}"
}

# Hàm xử lý các chủ đề cụ thể
process_message() {
    # Chào hỏi
    if [[ "$LOWER_MESSAGE" =~ ^(xin chào|chào|hello|hi|hey|helo)$ ]]; then
        local greetings=(
            "Xin chào! Rất vui được nói chuyện với bạn! 👋"
            "Chào bạn! Hôm nay bạn thế nào? 😊"
            "Hello! Mình là Chat Agent, có thể giúp gì cho bạn?"
            "Hi! Chào mừng bạn đến với chat client! 🎉"
        )
        get_random_response "${greetings[@]}"
        return
    fi
    
    # Hỏi tên
    if [[ "$LOWER_MESSAGE" =~ (tên|name|gọi) ]] && [[ "$LOWER_MESSAGE" =~ (gì|what|là) ]]; then
        echo "Mình là Chat Agent, một trợ lý ảo được viết bằng Bash Script! 🤖"
        return
    fi
    
    # Hỏi về thời tiết
    if [[ "$LOWER_MESSAGE" =~ (thời tiết|weather|trời) ]]; then
        local weather=(
            "Thời tiết hôm nay đẹp lắm! Nắng ấm khoảng 28°C ☀️"
            "Trời đang mưa nhẹ, nhớ mang ô nhé! ☔"
            "Hôm nay trời nhiều mây, mát mẻ dễ chịu 🌤️"
            "Nắng gắt quá! Nhớ uống nhiều nước nhé! 🌡️"
        )
        get_random_response "${weather[@]}"
        return
    fi
    
    # Hỏi về hệ điều hành / Linux
    if [[ "$LOWER_MESSAGE" =~ (hệ điều hành|linux|os|ubuntu|bash) ]]; then
        local os_responses=(
            "Linux rất mạnh mẽ! Bash scripting là kỹ năng quan trọng đấy! 🐧"
            "Hệ điều hành là nền tảng của mọi phần mềm! Bạn đang học môn này à?"
            "Bash script thật tuyệt phải không? Mình được tạo ra từ Bash đấy! 💻"
            "Operating System là một trong những môn khó nhưng rất thú vị!"
        )
        get_random_response "${os_responses[@]}"
        return
    fi
    
    # Hỏi về học tập
    if [[ "$LOWER_MESSAGE" =~ (học|study|bài tập|assignment|homework) ]]; then
        local study=(
            "Chúc bạn học tập tốt! Cố gắng lên nhé! 📚"
            "Làm bài tập cần kiên nhẫn! Bạn đang làm tốt đấy! 💪"
            "Học hành vất vả nhỉ? Nghỉ ngơi đúng lúc cũng quan trọng đấy!"
            "Hệ điều hành là môn hay! Chúc bạn điểm cao! 🎓"
        )
        get_random_response "${study[@]}"
        return
    fi
    
    # Cảm xúc tích cực
    if [[ "$LOWER_MESSAGE" =~ (vui|happy|tốt|good|great|tuyệt) ]]; then
        local positive=(
            "Tuyệt vời! Mình cũng vui khi bạn vui! 😄"
            "Thật tuyệt! Hãy giữ tinh thần tích cực nhé! ✨"
            "Yeah! Năng lượng tích cực là điều tuyệt vời! 🌟"
            "Mình rất vui khi nghe điều đó! 🎉"
        )
        get_random_response "${positive[@]}"
        return
    fi
    
    # Cảm xúc tiêu cực
    if [[ "$LOWER_MESSAGE" =~ (buồn|sad|mệt|tired|khó|difficult) ]]; then
        local supportive=(
            "Đừng lo! Mọi chuyện sẽ ổn thôi! 💙"
            "Nghỉ ngơi một chút nhé! Bạn đã cố gắng rất tốt rồi! 🌈"
            "Khó khăn chỉ là tạm thời! Cố lên bạn nhé! 💪"
            "Mình luôn ở đây lắng nghe bạn! Chia sẻ thêm đi!"
        )
        get_random_response "${supportive[@]}"
        return
    fi
    
    # Hỏi về thời gian
    if [[ "$LOWER_MESSAGE" =~ (giờ|time|mấy giờ) ]]; then
        local current_time=$(date '+%H:%M:%S')
        echo "Bây giờ là $current_time đấy! ⏰"
        return
    fi
    
    # Hỏi về ngày
    if [[ "$LOWER_MESSAGE" =~ (ngày|date|hôm nay) ]]; then
        local current_date=$(date '+%d/%m/%Y')
        echo "Hôm nay là ngày $current_date! 📅"
        return
    fi
    
    # Cảm ơn
    if [[ "$LOWER_MESSAGE" =~ (cảm ơn|thanks|thank you|cám ơn) ]]; then
        local thanks=(
            "Không có gì! Rất vui được giúp bạn! 😊"
            "Luôn sẵn sàng! Cần gì cứ nói nhé! 👍"
            "Hehe, đó là nhiệm vụ của mình mà! 🤗"
            "You're welcome! Anytime! ✨"
        )
        get_random_response "${thanks[@]}"
        return
    fi
    
    # Tạm biệt
    if [[ "$LOWER_MESSAGE" =~ ^(bye|tạm biệt|goodbye|bb)$ ]]; then
        local goodbyes=(
            "Tạm biệt! Hẹn gặp lại bạn sau nhé! 👋"
            "Bye bye! Chúc bạn một ngày tốt lành! 🌸"
            "See you! Quay lại chat với mình nha! 💫"
            "Hẹn gặp lại! Take care! 🌈"
        )
        get_random_response "${goodbyes[@]}"
        return
    fi
    
    # Câu hỏi về con người
    if [[ "$LOWER_MESSAGE" =~ \? ]]; then
        local questions=(
            "Đó là một câu hỏi hay! Để mình suy nghĩ... 🤔"
            "Hmm, câu hỏi thú vị đấy! Bạn nghĩ sao về nó?"
            "Wow, mình chưa nghĩ về điều đó! Góc nhìn của bạn thế nào?"
            "Câu hỏi sâu sắc đấy! Bạn tò mò về điều này lắm phải không?"
        )
        get_random_response "${questions[@]}"
        return
    fi
    
    # Response mặc định
    get_random_response "${GENERAL_RESPONSES[@]}"
}

# Main: Xử lý và trả về response
if [ -z "$USER_MESSAGE" ]; then
    echo "❌ Lỗi: Không nhận được tin nhắn!"
else
    process_message
fi