# Auto Bypass — Link4m

Web app dùng FastAPI và Playwright Chromium để xử lý các bước chuyển hướng thông thường của Link4m. Công cụ không giải CAPTCHA, không né hệ thống chống bot và không truy cập URL mạng nội bộ.

## Yêu cầu

- Python 3.11
- Chromium dependencies (Playwright có thể cài bằng lệnh bên dưới)

## Chạy local trên Windows / Linux

    python -m venv .venv
    # Windows: .venv\Scripts\activate
    # Linux/macOS: source .venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium
    uvicorn app.main:app --reload

Mở http://127.0.0.1:8000. API docs tại http://127.0.0.1:8000/docs.

## Chạy test

    pytest -q

## Docker

    docker build -t bypass-4m .
    docker run --rm -p 8000:8000 -e PORT=8000 bypass-4m

## Deploy Render

1. Push repository lên GitHub.
2. Trong Render, chọn New → Blueprint và kết nối repository.
3. Render đọc render.yaml, build Docker image và triển khai web service.
4. Kiểm tra /api/health sau khi deploy.

Render Free có thể sleep khi không có traffic và cold start khi được gọi lại. RAM và thời gian build phụ thuộc image/dependencies thực tế; Chromium có thể vượt giới hạn tài nguyên của gói Free. Không cam kết mọi lượt xử lý sẽ chạy thành công trên Free tier.

## API

- GET /api/health: trạng thái ứng dụng.
- POST /api/bypass: body JSON gồm trường url, ví dụ https://link4m.net/...

## Giới hạn an toàn

- Chỉ nhận URL ban đầu thuộc link4m.net hoặc www.link4m.net.
- Chặn request tới IP private, loopback, link-local và hostname nội bộ.
- Kiểm tra request phát sinh trong browser.
- Một browser job tại một thời điểm; request đồng thời nhận HTTP 429.
- Timeout tổng 90 giây.
- Chỉ tự động click các nút điều hướng phổ biến; CAPTCHA hoặc xác minh thủ công sẽ trả lỗi.

## Ghi chú

Link4m có thể thay đổi giao diện hoặc luồng điều hướng. Cần kiểm thử bằng link công khai được phép sử dụng trước khi coi engine tương thích hoàn toàn. Health endpoint xác nhận ứng dụng phản hồi, không phải phép thử khởi động Chromium.
