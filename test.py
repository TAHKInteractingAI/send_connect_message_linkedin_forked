# import os
# import time
# from selenium import webdriver
# from dotenv import load_dotenv
# from selenium.webdriver.chrome.options import Options

# load_dotenv()

# # Cấu hình Chrome cho GitHub Actions (Headless)
# options = Options()
# options.add_argument("--headless=new")
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-dev-shm-usage")

# driver = webdriver.Chrome(options=options)

# def login_with_cookie():
#     # Bước 1: Phải vào trang chủ để trình duyệt nhận diện Domain trước
#     driver.get("https://www.linkedin.com")
#     time.sleep(2) # Đợi một chút để trang load sơ bộ

#     li_at_cookie = os.getenv("LINKEDIN_COOKIE")
    
#     if li_at_cookie:
#         # Xóa các cookie rác hiện có để tránh xung đột
#         driver.delete_all_cookies()
        
#         # Bước 2: Thêm Cookie với cấu hình chi tiết hơn
#         driver.add_cookie({
#             "name": "li_at",
#             "value": li_at_cookie,
#             "domain": ".linkedin.com", # Quan trọng: Phải có dấu chấm ở đầu
#             "path": "/",
#             "secure": True
#         })
        
#         # Bước 3: Refresh lại trang để LinkedIn nhận diện phiên đăng nhập
#         driver.get("https://www.linkedin.com/feed/") # Đi thẳng vào trang Feed thay vì trang chủ
#         time.sleep(5)
        
#         print("INFO: Đã thực hiện add Cookie!")
#     else:
#         print("ERROR: Không tìm thấy LINKEDIN_COOKIE")

# # Thực thi
# login_with_cookie()

# # Test xem đã vào được chưa
# print(f"Tiêu đề trang hiện tại: {driver.title}")

# driver.quit()