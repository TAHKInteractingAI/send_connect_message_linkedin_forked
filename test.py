# # from dotenv import load_dotenv
# # import os, json
# # import gspread
# # import pandas as pd
# # from oauth2client.service_account import ServiceAccountCredentials
# # load_dotenv()

# # SPREADSHEET_ID = os.getenv('SPREADSHEET_MESS_ID')
# # SHEET_NAME = 'Sheet1'
# # RANGE_NAME = 'A:E'
# # GOOGLE_CREDS = os.getenv('GOOGLE_APPLICATION_CRED')

# # # Xác thực với Google Sheets API
# # scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# # info = json.loads(GOOGLE_CREDS)
# # creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
# # client = gspread.authorize(creds)

# # # Lấy dữ liệu từ bảng tính
# # sheet = client.open_by_key(SPREADSHEET_ID).worksheet('Sheet1')
# # values = sheet.get_all_values()
# # df = pd.DataFrame(values[1:], columns=values[1])
# # for index, row in df.iterrows():
# #     print(index, row)
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