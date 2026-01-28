# Sử dụng bản slim nhưng cần cài thêm các công cụ hỗ trợ
FROM python:3.9-slim

# Cài đặt các gói phụ thuộc và thêm kho lưu trữ Google Chrome
RUN apt-get update && apt-get install -y wget gnupg curl unzip --no-install-recommends \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy file requirements và cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code
COPY . .

# Port mặc định của Render là 10000 hoặc dùng biến môi trường PORT
CMD ["uvicorn", "copy_of_connect_linkedin_with_cookie:app", "--host", "0.0.0.0", "--port", "10000"]