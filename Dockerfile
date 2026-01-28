FROM python:3.9-slim

# Cài đặt Chrome và các thư viện hệ thống cần thiết cho Selenium
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl \
    google-chrome-stable \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Cài đặt thư viện Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào
COPY . .

# Chạy lệnh khởi động API
CMD ["uvicorn", "copy_of_connect_linkedin_with_cookie:app", "--host", "0.0.0.0", "--port", "10000"]