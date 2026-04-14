
import json
import os
import time
import undetected_chromedriver as uc
import random, pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
#from IPython.display import Image, display
from oauth2client.service_account import ServiceAccountCredentials
import requests
import pandas as pd
from dotenv import load_dotenv
import gspread
from gspread.exceptions import APIError
from pathlib import Path

load_dotenv(override=True)

"""# **CONFIG**"""
MAX_RETRIES = 3
MISSIVE_API_KEY = os.getenv('MISSIVE_API_KEY')
MAX_MESSAGES_PER_DAY = 15
COOKIES_FILE = 'linkedin_cookies.pkl'
HEADERS = {"Authorization": f"Bearer {MISSIVE_API_KEY}", "Content-Type": "application/json"}
PARAMS = {"limit": 20, "inbox":"true"} 
# Thông tin bảng tính
SPREADSHEET_ID = os.getenv('SPREADSHEET_MESS_ID')
SHEET_NAME = 'Sheet1'
RANGE_NAME = 'A:E'
GOOGLE_CREDS = os.getenv('GOOGLE_APPLICATION_CRED')
TARGET_URL = "https://www.linkedin.com/uas/login?session_redirect=https%3A%2F%2Fwww.linkedin.com%2Ffeed%2F"

"""# **XPATH**"""

# XPATH ỨNG VỚI NÚT MESSAGE.
BUTTON_MESSAGE = "/html/body/div/div[2]/div[2]/div[2]/div/main/div/div/div[1]/div/div/div[1]/div/div/section/div/div/div[2]/div[3]/div/div/div[1]/a/span/span[contains(text(), 'Message')] | /html/body/div/div[2]/div[2]/div[2]/div/main/div/div/div[1]/div/div/div[1]/div/div/section/div/div/div[2]/div[3]/div/div/div[2]/a | /html/body/div[6]/div[3]/div/div/div[2]/div/div/main/section[1]/div[2]/div[3]/div/div[1]/button[contains(@aria-label, 'Message')] | /html/body/div/div[2]/div[2]/div[2]/div/main/div/div/div[1]/div/div/div[1]/div/section/div/div/div[2]/div[3]/div/div/div[1]/a | /html/body/div/div[2]/div[2]/div[2]/div/main/div/div/div[1]/div/div/div[1]/div/section/div/div/div[2]/div[3]/div/div/div[2]/a"  #Đổi sang full XPATH (dễ lỗi hơn nếu có updated từ linkedin)
# XPATH ỨNG VỚI KHUNG TIN NHẮN. (CLASS NAME)
CLASS_FIELD_MESSAGE = "msg-form__contenteditable"
# CLASS ỨNG VỚI KHUNG ĐÍNH KÈM TỆP. (CLASS NAME)
CLASS_FIELD_ATTACHMENT = "msg-form__attachment-upload-input"
#XPATH CÁC FILE ATTACH
XPATH_FILE_ATTACH_BTN = "//button[contains(@title, 'Attach a file to your conversation with') or contains(@aria-label, 'Attach a file to your conversation with')]"
XPATH_FILE_ATTACH = f"//input[@type='file' and contains(@class, {CLASS_FIELD_ATTACHMENT})]"
# XPATH ỨNG VỚI NÚT GỬI TIN NHẮN. (CLASS NAME)
XPATH_BUTTON_SUBMIT_MESSAGE = "msg-form__send-button"
# XPATH ỨNG VỚI NÚT ĐÓNG HỘP THOẠI NHẮN TIN.
XPATH_BUTTON_CLOSE_MESSAGE = "/html/body/div[6]/div[4]/aside[1]/div[2]/div[1]/header/div[4]/button[3]"
# XPATH cập nhật (LinkedIn thường xuyên đổi ID nên dùng Class hoặc Text ổn định hơn)
FIELD_MESSAGE_CLASS = "msg-form__contenteditable"
BUTTON_SEND_CLASS = "msg-form__send-button"
XPATH_ACCEPT_BUTTON = "//button[span[text()='Accept']]"
# Login fields/buttons
XPATH_USERNAME = '//*[@id="username"]' #| //input[@id=":r3:"] | //input[contains(@id, "r")] | //input[@autocomplete="username" or @autocomplete="webauthn"]'
XPATH_PASSWORD = '//*[@id="password"]'# | //input[@id=":r4:"] | //input[contains(@id, "r")] | //input[@autocomplete="current-password"]'
XPATH_LOGIN_BUTTON = '//button[contains(@class, "btn__primary--large") and @aria-label="Sign in"]'#| //button[.//text()[contains(., "Sign in") or contains(., "Log in") or contains(., "Đăng nhập")]]'
# Message/send related
SEND_BUTTON_XPATH = "//button[contains(@class, 'msg-form__send-button')] | //button[text()='Send']"


"""# **HÀM HỖ TRỢ**"""
def press_multiple_tab(actions,number_of_presses, wait_time):
    for i in range(number_of_presses):
        actions.send_keys(Keys.TAB).perform()
        time.sleep(wait_time)
        
def shift_tab(actions, wait_time):
    actions.key_down(Keys.LEFT_SHIFT).send_keys(Keys.TAB).key_up(Keys.LEFT_SHIFT).perform()
    time.sleep(wait_time)
    
def get_missive_linkedin_code():
    response = requests.get("https://public.missiveapp.com/v1/conversations", headers=HEADERS, params=PARAMS)
    if response.status_code != 200:
        return f"Lỗi API: {response.status_code}"
    conversations = response.json().get("conversations", [])
    temp = [c['latest_message_subject'] for c in conversations if 'name' in c['authors'][0] and c['authors'][0]['name'] == 'LinkedIn']
    final_temp = [f.split(' ')[-1:][0] for f in temp]
    for item in final_temp:
        if item.isdigit():
            return item
    return None

# def restore_cookie_from_secret():
#     raw_cookie = os.getenv('RAW_COOKIE_BASE64')
#     # Chỉ tạo file nếu chưa có (để ưu tiên cache của GitHub)
#     if raw_cookie and not os.path.exists('linkedin_cookies.pkl'):
#         with open('linkedin_cookies.pkl', 'wb') as f:
#             f.write(base64.b64decode(raw_cookie))
#         print("✅ Đã tạo file linkedin_cookies.pkl từ GitHub Secret!")
        
def human_type(element, text):
    """Gõ phím như người thật với độ trễ ngẫu nhiên"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))
def random_delay(min_s=2, max_s=5):
    time.sleep(random.uniform(min_s, max_s))
# def get_data_with_links_return_with_attachment_url(sheet):
#     # 1. Lấy toàn bộ giá trị của bảng tính (để biết chính xác số dòng hiện có)
#     all_values = sheet.get_all_values()
#     if len(all_values) < 2:
#         return pd.DataFrame()

#     headers = all_values[0]  # Dòng 2 (index 1) là header
#     data_rows = all_values[1:] # Dữ liệu thực tế từ dòng 2
#     num_rows = len(data_rows)

#     # 2. Lấy metadata của cột E (Attachment) - Giả sử là cột số 5
#     # Chỉ lấy đúng phạm vi tương ứng với số dòng dữ liệu đang có
#     spreadsheet = sheet.spreadsheet
#     sheet_name = sheet.title
#     range_metadata = f"{sheet_name}!E2:E{1 + num_rows}"
    
#     res_metadata = spreadsheet.fetch_sheet_metadata({
#         'includeGridData': True,
#         'ranges': [range_metadata]
#     })
    
#     links_per_row = []
#     # Truy cập vào cấu trúc dữ liệu JSON của Google
#     sheets_data = res_metadata.get('sheets', [])[0].get('data', [])[0]
#     rowData = sheets_data.get('rowData', [])
    
#     for row in rowData:
#         cell_links = []
#         values = row.get('values', [])
#         if values:
#             cell = values[0]
#             # Ưu tiên 1: Link bao trùm toàn bộ ô
#             if 'hyperlink' in cell:
#                 cell_links.append(cell['hyperlink'])
#             # Ưu tiên 2: Nhiều link trong các đoạn văn bản (Rich Text)
#             elif 'textFormatRuns' in cell:
#                 for run in cell['textFormatRuns']:
#                     url = run.get('format', {}).get('link', {}).get('uri')
#                     if url:
#                         cell_links.append(url)
        
#         # Gộp các link, loại bỏ trùng lặp bằng set
#         unique_links = list(dict.fromkeys(cell_links))
#         links_per_row.append(", ".join(unique_links))

#     # 3. Đảm bảo links_per_row có độ dài bằng với data_rows
#     # Nếu metadata trả về thiếu, bù cho đủ bằng chuỗi rỗng
#     while len(links_per_row) < num_rows:
#         links_per_row.append("")

#     # 4. Tạo DataFrame
#     df = pd.DataFrame(data_rows, columns=headers)
    
#     # Cập nhật cột Attachment (cần chắc chắn tên cột đúng 100% với file Sheets)
#     if 'Attachment' in df.columns:
#         df['Attachment'] = links_per_row[:num_rows]
    
#     return df
def get_data_with_links(sheet):
    def call_with_retry(func, *args, **kwargs):
        for attempt in range(5):  # Max 5 attempts
            try:
                return func(*args, **kwargs)
            except APIError as e:
                if e.response.status_code in [503, 429]:
                    wait_time = (2 ** attempt)  # 1, 2, 4, 8 seconds
                    print(f"Google API {e.response.status_code} error. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise e
        return func(*args, **kwargs)
    all_values = call_with_retry(sheet.get_all_values)
    if len(all_values) < 2:
        return pd.DataFrame()

    headers = all_values[0]
    data_rows = all_values[1:]
    num_rows = len(data_rows)

    spreadsheet = sheet.spreadsheet
    sheet_name = sheet.title
    range_metadata = f"{sheet_name}!E2:E{1 + num_rows}"
    res_metadata = call_with_retry(spreadsheet.fetch_sheet_metadata, {'includeGridData': True, 'ranges': [range_metadata]})
    # res_metadata = spreadsheet.fetch_sheet_metadata({
    #     'includeGridData': True,
    #     'ranges': [range_metadata]
    # })
    
    file_names_per_row = []
    sheets_data = res_metadata.get('sheets', [])[0].get('data', [])[0]
    rowData = sheets_data.get('rowData', [])
    if not rowData:
        return pd.DataFrame(data_rows, columns=headers)
    
    for row in rowData:
        names = []
        values = row.get('values', [])
        if values:
            cell = values[0]
            full_text = cell.get('formattedValue', '')
            
            # Trường hợp 1: Link bao phủ toàn bộ ô
            if 'hyperlink' in cell:
                names.append(full_text)
            
            # Trường hợp 2: Rich Text (Nhiều file/link trong 1 ô)
            elif 'textFormatRuns' in cell:
                runs = cell['textFormatRuns']
                for i in range(len(runs)):
                    run = runs[i]
                    # Kiểm tra xem đoạn text này có chứa link không
                    url = run.get('format', {}).get('link', {}).get('uri')
                    if url:
                        start = run.get('startIndex', 0)
                        # Kết thúc là startIndex của run kế tiếp hoặc cuối chuỗi
                        end = runs[i+1].get('startIndex') if i + 1 < len(runs) else len(full_text)
                        
                        file_name = full_text[start:end].strip(", \n")
                        if file_name:
                            names.append(file_name)
        
        # Gộp các tên file, phân cách bằng dấu phẩy
        file_names_per_row.append(", ".join(dict.fromkeys(names)))

    while len(file_names_per_row) < num_rows:
        file_names_per_row.append("")

    df = pd.DataFrame(data_rows, columns=headers)
    if 'Attachment' in df.columns:
        df['Attachment'] = file_names_per_row[:num_rows]
    
    return df

def save_cookies(driver):
    """Lưu cookies vào file"""
    with open(COOKIES_FILE, "wb") as cookies_file:
        pickle.dump(driver.get_cookies(), cookies_file)
    print("INFO: COOKIES SAVED!")

def load_cookies(driver: webdriver.Chrome, file_name: str):
    """Đọc cookies từ file pickle và thêm vào browser"""
    if os.path.exists(file_name):
        with open(file_name, 'rb') as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
                
# def display_screenshot(driver: webdriver.Chrome, file_name: str = 'screenshot.png'):
#     driver.save_screenshot(file_name)
#     time.sleep(5)
#     display(Image(filename=file_name))


# def capture_full_page_screenshot(driver: webdriver.Chrome, file_name: str = 'full_screenshot.png'):
#     # Cấu hình lại kích thước cửa sổ để chụp toàn màn hình
#     total_width = driver.execute_script("return document.body.scrollWidth")
#     total_height = driver.execute_script("return document.body.scrollHeight")
#     driver.set_window_size(total_width, total_height)

#     # Chụp ảnh màn hình với kích thước đã cấu hình
#     driver.save_screenshot(file_name)

#     # Hiển thị ảnh đã chụp
#     time.sleep(2)
#     display(Image(filename=file_name))

"""# **KẾT NỐI GOOGLE SHEETS**"""

# Xác thực với Google Sheets API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
info = json.loads(GOOGLE_CREDS)
creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
client = gspread.authorize(creds)

# Lấy dữ liệu từ bảng tính
sheet = client.open_by_key(SPREADSHEET_ID).worksheet('Sheet1')
values = sheet.get_all_values()
#df = pd.DataFrame(values[2:], columns=values[1])
df = get_data_with_links(sheet)
#print(df)

"""# **HIỂN THỊ THÔNG TIN GOOGLE SHEETS**"""

# df.head()

"""# **CẤU HÌNH DRIVER**"""
# def get_driver():
#     options = webdriver.ChromeOptions()
    
#     # 1. Định nghĩa một User-Agent nhất quán (Tránh khai báo 2 lần)
#     user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#     options.add_argument(f"user-agent={user_agent}")

#     # 2. Các thiết lập cơ bản cho môi trường Linux/Docker (GitHub Actions)
#     options.add_argument('--no-sandbox')
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument('--disable-gpu')
#     options.add_argument('--headless=new')
#     options.add_argument("--window-size=1920,1080")
    
#     # 3. CHỐNG PHÁT HIỆN BOT (Stealth Mode)
#     # Loại bỏ cờ 'nút điều khiển tự động'
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option('useAutomationExtension', False)
#     # Vô hiệu hóa tính năng AutomationControlled của Blink
#     options.add_argument("--disable-blink-features=AutomationControlled")
    
#     # Thêm các cờ để trình duyệt giống người dùng thật hơn
#     options.add_argument("--disable-infobars")
#     options.add_argument("--disable-notifications")
    
#     # Khởi tạo driver
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=options)
    
#     # 4. Ẩn thuộc tính navigator.webdriver bằng Script thực thi ngay khi load trang
#     driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
#         "source": """
#             Object.defineProperty(navigator, 'webdriver', {
#                 get: () => undefined
#             })
#         """
#     })
    
#     return driver
def get_driver():
    options = uc.ChromeOptions()
    
    # 1. Cấu hình cơ bản cho môi trường Headless (GitHub Actions)
    #options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1920,1080")
    
    # 2. [TĂNG TỐC] Chiến lược load trang
    # 'eager' giúp trình duyệt không chờ đợi tải xong ảnh hay script bên thứ 3
    options.page_load_strategy = 'eager'
    
    # 3. [TĂNG TỐC] Chặn tải hình ảnh, CSS và Fonts để tiết kiệm băng thông và RAM
    # prefs = {
    #     "profile.managed_default_content_settings.images": 2,
    #     "profile.managed_default_content_settings.stylesheets": 2,
    #     "profile.managed_default_content_settings.fonts": 2
    # }
    # options.add_experimental_option("prefs", prefs)
    
    # 4. Ép trình duyệt dùng tiếng Anh
    options.add_argument('--lang=en-GB')
    
    # 5. [CHỐNG PHÁT HIỆN] Thêm Proxy dân cư (Khuyến nghị)
    # Trên GitHub Actions, hãy set secrets.PROXY_URL (ví dụ: http://user:pass@ip:port)
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        options.add_argument(f'--proxy-server={proxy_url}')
    
    # Khởi tạo undetected_chromedriver (Không dùng webdriver.Chrome thông thường)
    driver = uc.Chrome(options=options, version_main=146)
    
    # 6. [CHỐNG PHÁT HIỆN] Bơm thêm Stealth Script qua CDP
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            // Ẩn webdriver
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            
            // Fake runtime của Chrome (Bot thường không có cái này)
            window.navigator.chrome = { runtime: {} };
            
            // Bơm thêm plugins giả
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Ép ngôn ngữ
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-GB', 'en-US', 'en']
            });
        """
    })
    
    return driver

"""# **HÀM ĐĂNG NHẬP**"""
                
def handle_cookie_acceptance(driver: webdriver.Chrome):
    try:
        driver.find_element(By.XPATH, XPATH_ACCEPT_BUTTON).click()
        print("INFO: COOKIES IS ACCEPTED!")
    except Exception:
        print("INFO: COOKIES IS NOT REQUIRED!")

def handle_code_verification(driver: webdriver.Chrome):
    try:        
        # FIND VERIFICATION FIELD.
        ID_FIELD = "input__email_verification_pin"
        CONDITION = EC.presence_of_element_located((By.ID, ID_FIELD))
        verification_field = WebDriverWait(driver, 20).until(CONDITION)
        # FIND SUBMIT BUTTON.
        ID_FIELD = "email-pin-submit-button"
        CONDITION = EC.presence_of_element_located((By.ID, ID_FIELD))
        submit_button = WebDriverWait(driver, 20).until(CONDITION)
        # ENTER VERIFICATION CODE.
        code = get_missive_linkedin_code()#input("Verification code required! Check your email and enter the code: ")
        print(f"Verification code: {code}")
        driver.save_screenshot("before_verification.png")
        time.sleep(2)
        verification_field.send_keys(code)
        time.sleep(3)
        submit_button.click()
        time.sleep(5)
    except Exception as e:
        print("INFO: NO VERIFICATION DETECTED!")
        print(e)

def login(driver: webdriver.Chrome, username: str, password: str):
    """Đăng nhập vào LinkedIn với username và password mới nếu có sự thay đổi"""
    # Use module-level XPATH constants defined at top

    driver.get(TARGET_URL)
    time.sleep(2)  # Ensure the page is fully loaded
    print(f"URL login: {driver.current_url}")
    # Kiểm tra nếu có cookies và kiểm tra xem username, password có thay đổi không
    #credentials = load_credentials()

    if os.path.exists(COOKIES_FILE):# and credentials:
        # Kiểm tra nếu username hoặc password đã thay đổi
        #if credentials['username'] == username and credentials['password'] == password:
            # Tải cookies và thử đăng nhập
        load_cookies(driver, COOKIES_FILE)
        driver.refresh()
        time.sleep(10)

        # Kiểm tra xem đã đăng nhập chưa bằng cách xem có biểu tượng người dùng không
        # try:
        #     user_icon = WebDriverWait(driver, 20).until(
        #         EC.presence_of_element_located((By.CLASS_NAME, 'global-nav__me-photo')))
        #     print("INFO: Logged in using cookies!")
        #     driver.save_screenshot("cookie-login.png")
        #     # save user_icon
        #     #user_icon.screenshot("user_icon.png")
        #     # display_screenshot(driver, "status.png")
        #     return
        # except Exception as e:
        #     print(f"INFO: Đăng nhập Cookie không thành công: {e}")
        #     os.remove(COOKIES_FILE)
        print(f"Current url: {driver.current_url}")
        if "linkedin.com/login" in driver.current_url or "checkpoint" in driver.current_url:
            print(f"INFO: Đăng nhập Cookie không thành công")
            os.remove(COOKIES_FILE)
        else:
            print("Đăng nhập cookie ok")
            return
    else:
        print("INFO: Không có file cookies")
        
    print("INFO: Bắt đầu login thủ công")
    driver.get("https://www.linkedin.com/login")
    time.sleep(5)
    if "feed" in driver.current_url.lower():
        print(f"SUCCESS: Đã tự động vào Feed tại {driver.current_url}. Bỏ qua bước nhập pass.")
        save_cookies(driver)
        return
    driver.save_screenshot("before_input.png")
    username_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, XPATH_USERNAME)))
    password_field = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, XPATH_PASSWORD)))
    login_button = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, XPATH_LOGIN_BUTTON)))
    
    human_type(username_field, username)
    #username_field.send_keys(username)
    time.sleep(2)
    human_type(password_field, password)
    #password_field.send_keys(password)
    time.sleep(2)
    login_button.click()

    time.sleep(10)
    driver.save_screenshot("before_verification.png")
    handle_code_verification(driver)
    handle_cookie_acceptance(driver)
    # Lưu cookies và thông tin đăng nhập sau khi đăng nhập thành công
    save_cookies(driver)
    #save_credentials(username, password)
    print("INFO: Đăng nhập thành công và đã lưu cookies, thông tin đăng nhập!")
    driver.save_screenshot("post-login.png")
        



"""# **HÀM GỬI TIN NHẮN**"""
# def check_datum(datum):
#     # KIỂM TRA TÊN.
#     name = datum["Name"]
#     if not name:
#         print("ERROR: NAME NOT FOUND!")
#         return "ERROR: NAME NOT FOUND!"
#     # KIỂM TRA TIN NHẮN.
#     message = datum["Message"]
#     if not message:
#         print("ERROR: MESSAGE NOT FOUND!")
#         return "ERROR: MESSAGE NOT FOUND!"
#     # KIỂM TRA TỆP ĐÍNH KÈM. (XỮ LÍ ĐA NỀN TẢNG)
#     #attachment = datum["Attachment"]
#     # !wget https://github.com/InteractingAI/Automatic_Colab/blob/main/HenryUniversesResume.pdf
#     # !wget https://github.com/InteractingAI/Automatic_Colab/blob/main/tokyo-vigil-436805-j9-d6e61a754dce.json
#     attachment_name = datum.get("Attachment")
#     abs_path = None
#     if attachment_name and str(attachment_name).strip():
#         # Lấy thư mục gốc nơi script đang chạy (tương thích cả Local và Server)
#         # Nếu chạy trên GitHub Actions, nó sẽ là thư mục repo
#         base_path = Path(__file__).parent.absolute()
#         file_path = base_path / attachment_name
        
#         if file_path.exists():
#             abs_path = str(file_path)
#             print(f"INFO: Attachment found at: {abs_path}")
#         else:
#             print(f"WARNING: File {attachment_name} không tồn tại tại {base_path}. Sẽ gửi tin không đính kèm.")
    
#     # url = '/content/' + attachment
#     # print(url)
#     # if attachment:
#     #     rel_path = os.path.join(attachment)
#     #     abs_path = os.path.abspath(rel_path)
#     #     if not os.path.exists(abs_path):
#     #         print("ERROR: ATTACHMENT NOT FOUND!")
#     #         return "ERROR: ATTACHMENT NOT FOUND"
#     # XỬ LÝ TIN NHẮN.
#     message = message.replace("{{Name}}", name)

#     return name, message, abs_path

# def send_message(driver: webdriver.Chrome, target_profile, datum):
#     name, message, attachment = datum

#     try:
#         # TÌM KIẾM NÚT MỞ HỘP THOẠI TIN NHẮN.
#         c = EC.presence_of_element_located((By.XPATH, BUTTON_MESSAGE))
#         # capture_full_page_screenshot(driver)
#         try:
#             e = WebDriverWait(driver, 15).until(c)
#         except:
#             print("ERROR: OPEN BUTTON NOT FOUND!")
#             return "ERROR: OPEN BUTTON NOT FOUND!"
#         # KIỂM TRA NÚT CÓ PHẢI LÀ NÚT MỞ HỘP THOẠI TIN NHẮN.
#         status = e.get_attribute("aria-label")
#         if "Message" not in status:
#             print("ERROR: BUTTON IS NOT MESSAGE BUTTON!")
#             return "ERROR: BUTTON IS NOT MESSAGE BUTTON!"
#         # NHẤN NÚT.
#         e.click()
#         time.sleep(2)
#         # capture_full_page_screenshot(driver)
#         # TÌM KIẾM KHUNG TIN NHẮN.
#         try:
#             e = driver.find_element(By.CLASS_NAME, FIELD_MESSAGE)
#             # capture_full_page_screenshot(driver)
#         except NoSuchElementException:
#             print("ERROR: MESSAGE BOX NOT FOUND!")
#             return "ERROR: MESSAGE BOX NOT FOUND!"
#         # XÓA TIN NHẮN MẶC ĐỊNH.
#         if e.text != "":
#             e.send_keys(Keys.CONTROL + "a")
#             e.send_keys(Keys.DELETE)
#             time.sleep(2)
#         # NHẬP TIN NHẮN.
#         e.send_keys(message)
#         time.sleep(2)
#         # capture_full_page_screenshot(driver)
#         if attachment:
#             # TÌM KIẾM KHUNG ĐÍNH KÈM.
#             try:
#                 e = driver.find_element(By.CLASS_NAME, FIELD_ATTACHMENT)
#             except NoSuchElementException:
#                 print("ERROR: ATTACHMENT BOX NOT FOUND!")
#                 return "ERROR: ATTACHMENT BOX NOT FOUND!"
#             # ĐÍNH KÈM TỆP.
#             e.send_keys(attachment)
#             # capture_full_page_screenshot(driver)
#             #display_screenshot(driver)
#             time.sleep(2)

#         # TÌM KIẾM NÚT GỬI TIN NHẮN.
#         c = EC.presence_of_element_located((By.CLASS_NAME, BUTTON_SUBMIT_MESSAGE))
#         try:
#             e = WebDriverWait(driver, 15).until(c)
#             driver.execute_script("arguments[0].click();", e)
#             # capture_full_page_screenshot(driver)
#         except:
#             print("ERROR: SUBMIT BUTTON NOT FOUND!")
#             return "ERROR: SUBMIT BUTTON NOT FOUND!"
#         # NHẤN NÚT
#         time.sleep(2)

#         # TÌM KIẾM NÚT ĐÓNG HỘP THOẠI.
#         # c = EC.presence_of_element_located((By.XPATH, BUTTON_CLOSE_MESSAGE))
#         # try:
#         #     e = WebDriverWait(driver, 15).until(c)
#         #     display_screenshot(driver)
#         # except:
#         #     print("ERROR: CLOSE BUTTON NOT FOUND!")
#         #     return "ERROR: CLOSE BUTTON NOT FOUND!"
#         # # NHẤN NÚT.
#         # e.click()
#         # display_screenshot(driver)
#         # time.sleep(2)

#         return "MESSAGE HAS SENT!"
#     except Exception as e:
#         print("\n" + str(e))
#         return "ERROR: MESSAGE NOT SENT!"



# def solve_subject_field_with_gemini(image_path: str, max_entries: int = 3) -> str:
#     client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

#     # Read & encode image
#     with open(image_path, "rb") as f:
#         image_base64 = base64.b64encode(f.read()).decode("utf-8")

#     for attempt in range(1, max_entries + 1):
#         try:
#             response = client.models.generate_content(
#                 model="gemini-3-flash-preview",
#                 contents=[
#                     types.Content(
#                         role="user",                    
#                         parts=[
#                             types.Part(
#                                 text=(
#                                     "This is a linkedin image that contains the message box. "
#                                     "If there's an input field to type in subject, response 'YES', else response 'NO'."
#                                     "Only give me one-word response, nothing else."
#                                 )
#                             ),
#                             types.Part(
#                                 inline_data=types.Blob(
#                                     mime_type="image/png",
#                                     data=image_base64,
#                                 )
#                             ),
#                         ],
#                     )
#                 ],
#             )

#             # Safe extraction
#             return response.text.strip()

#         except ServerError as e:
#             if attempt < max_entries:
#                 time.sleep(3)
#             else:
#                 raise RuntimeError("Max retries reached. Gemini API unavailable.") from e

#     return None

def send_message_optimized(driver, row):
    try:
        actions = ActionChains(driver)
        name = row['Name']
        message_template = row['Message'].replace("{{Name}}", name if name != "" else "my friend")
            # Nối link vào cuối tin nhắn theo định dạng rõ ràng
        full_message = message_template
        #print(full_message)
        # attachment_path = None
        # if row.get('Attachment') and str(row.get('Attachment')).strip()!= "":
        #     attachment_path = os.path.abspath(row['Attachment'])
        try:
            find_close_bubble_shadow_js = """
                const host = document.querySelector('#interop-outlet');
                if (host && host.shadowRoot) {
                    const element = host.shadowRoot.querySelector('button.msg-overlay-bubble-header__control:has(svg[data-test-icon="close-small"][aria-hidden="true"])');
                    if (element) {
                        element.click();
                        return true;
                    }
                }
                return false;
            """
            driver.execute_script(find_close_bubble_shadow_js)
            print("Đã ấn nút thoát")
        except Exception:
            print(f"Không tìm thấy nút thoát bubble, tiếp tục")
            
        # TÌM NÚT MESSAGE
        try:
            msg_btn = WebDriverWait(driver, 10).until(
               EC.element_to_be_clickable((By.XPATH, BUTTON_MESSAGE))
            )
            print(f"Tìm thấy nút msg: {msg_btn}")
            msg_btn.click()
            time.sleep(3)
            driver.save_screenshot(f"message_box_found.png")
        except:
            print("Không tìm thấy nút msg với XPATH, bắt đầu actionChains")
            in_search_for_mess = True
            while in_search_for_mess:
                actions.send_keys(Keys.TAB).perform()
                time.sleep(0.5)
                mess_current_element = driver.switch_to.active_element
                mess_current_element_text = mess_current_element.text.strip()
                if mess_current_element_text in ["Message"]:
                    driver.execute_script("arguments[0].click();", mess_current_element)
                    in_search_for_mess = False
            print("Đã tìm thấy và click vào nút Message bằng ActionChains")
            driver.save_screenshot(f"message_box_found.png")
            #return "ERROR: MESSAGE BUTTON NOT FOUND"
        
        # current_element = driver.switch_to.active_element.get_attribute("class")
        # print(f"Current active element: {current_element}")
        
        # gemini_result = solve_subject_field_with_gemini("message_box_found.png")
        # print(gemini_result)
        # if gemini_result not in ['YES', 'NO']:
        #     print("WARNING: Gemini response không rõ ràng, mặc định sẽ nhấn TAB để thử kích hoạt trường nhập tin nhắn.")
        #     return "UNKNOWN"
        # if gemini_result == "YES":
        #     actions.send_keys(Keys.TAB).perform()
        #     time.sleep(0.5)
        shift_tab(actions, 0.3)
        active_text = driver.switch_to.active_element.text.lower()
        if any(word in active_text.split()[-1:] for word in ['connection', 'connections']):
            print("Hệ thống không tự động focus, đang di chuyển...")
            # for _ in range(34):
            #     shift_tab(actions, 0.5)
            find_msg_area_and_click_js = """
                const host = document.querySelector('#interop-outlet');
                if (host && host.shadowRoot) {
                    const element = host.shadowRoot.querySelector('div.msg-form__contenteditable');
                    if (element) {
                        element.focus(); // Focus trước khi làm việc khác
                        element.click();
                        return true;
                    }
                }
                return false;
            """
            try:
                # 2. Thực thi (Chỉ cần truyền 1 tham số là chuỗi script)
                driver.execute_script(find_msg_area_and_click_js)
                print("✅ Đã tìm thấy và click vào khung chat!")
            except Exception as e:
                print(f"INFO: {e}")
                for _ in range(0, 35):
                    shift_tab(actions, 0.5)
        else:
            print("Hệ thống đã tự động focus, lùi lại 1 step")
            actions.send_keys(Keys.TAB).perform()
            time.sleep(0.5)

        driver.save_screenshot("debug.png")
  
        actions.send_keys(full_message).perform()
        actions.send_keys(Keys.SPACE).perform()
        driver.save_screenshot('after_message.png')
        print("Nhập tin nhắn thành công, bắt đầu đính kèm tệp")
        time.sleep(6)
        
        #Bắt đầu đính kèm tệp
        # 1. Chuẩn bị file
        files_to_upload = [f.strip() for f in row['Attachment'].split(',')]
        base_path = Path(__file__).parent.absolute()
        print(f"INFO: {files_to_upload}")
        # 2. Script JavaScript để tìm input xuyên qua Shadow DOM
        # Script này sẽ tìm từ 'interop-outlet' và đi vào shadowRoot của nó
        find_input_in_shadow_js = """
            const host = document.querySelector('#interop-outlet');
            if (!host || !host.shadowRoot) return null;
            
            return host.shadowRoot.querySelector('input[type="file"]');
        """

        try:
            print("🔍 Đang tìm kiếm input bên trong Shadow DOM...")
            file_input = driver.execute_script(find_input_in_shadow_js)

            if file_input:
                print("✅ Đã tìm thấy element để input file!")

                # 3. Hiển thị input để Selenium có thể tương tác
                driver.execute_script("""
                    arguments[0].style.display = 'block';
                    arguments[0].style.visibility = 'visible';
                    arguments[0].style.opacity = '1';
                    arguments[0].classList.remove('hidden');
                """, file_input)

                # 4. Upload từng file
                for file_name in files_to_upload:
                    full_path = str(base_path / file_name)
                    if os.path.exists(full_path):
                        print(f"➡️ Đang gửi file: {full_path}")
                        file_input.send_keys(full_path)
                        time.sleep(2) # Đợi LinkedIn xử lý file
                    else:
                        print(f"File không tồn tại: {full_path}")
            else:
                print("Không tìm thấy input. Có thể bạn cần click vào nút kẹp giấy trước để nó render input.")

        except Exception as e:
            print(f"Lỗi: {e}")
        driver.save_screenshot("after_send_attachment_logic.png")
        try:
            # Tìm nút Gửi bằng XPATH linh hoạt (thường ổn định hơn Class)
            send_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, SEND_BUTTON_XPATH))
            )
            
            # Click bằng JavaScript để vượt qua các lớp đè (Overlay)
            driver.execute_script("arguments[0].click();", send_btn)
            print("INFO: Đã nhấn nút Gửi bằng JS")
            random_delay(2, 4)
            return "SUCCESS"
            
        except Exception as e:
            print(f"WARNING: Nút gửi không click được, thử Ctrl+Enter dự phòng: {e}")
            actions.key_down(Keys.CONTROL).send_keys(Keys.ENTER).key_up(Keys.CONTROL).perform()
            random_delay(2, 4)
            return "SUCCESS"
            
        # # ATTACHMENT (NẾU CÓ)
        # if attachment_path and os.path.exists(attachment_path):
        #     try:
        #         attach_input = driver.find_element(By.CLASS_NAME, "msg-form__attachment-upload-input")
        #         attach_input.send_keys(attachment_path)
        #         print(f"INFO: Đã đính kèm file: {row['Attachment']}")
        #         random_delay(3, 5)
        #     except Exception as e:
        #         print(f"WARNING: Có lỗi khi đính kèm nhưng vẫn sẽ gửi tin: {e}")
        # else:
        #     if attachment_path:
        #           print(f"WARNING: Không tìm thấy file {attachment_path}, bỏ qua đính kèm.")
        
        # GỬI
        # send_btn = driver.find_element(By.CLASS_NAME, BUTTON_SEND_CLASS)
        
        # if send_btn.is_enabled():
        #     send_btn.click()
        #     random_delay(2, 4)
        #     return "SUCCESS"
        # else:
        #     return "ERROR: SEND BUTTON DISABLED"
        
    except Exception as e:
        return f"ERROR: {str(e)}"
    
"""# **THỰC HIỆN GỬI TIN NHẮN**"""

def main_mess():
    """Luồng chính: Ưu tiên Cookie -> Login Manual -> Gửi tin nhắn"""
        
    driver = get_driver()
    
    username = os.getenv("LINKEDIN_USERNAME")
    password = os.getenv("LINKEDIN_PASSWORD")
    login(driver, username, password)
    """# **THỰC HIỆN GỬI KẾT NỐI**"""
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    
    
    send_count = 0
    sent_links = set()  # Tập hợp để theo dõi các link đã gửi trong phiên này
    
    for index, row in df.iterrows():
        print(f"=======================Starting================")
        # 1. Kiểm tra giới hạn hàng ngày
        if send_count >= MAX_MESSAGES_PER_DAY:
            print(f"INFO: Đã đạt giới hạn {MAX_MESSAGES_PER_DAY} người/ngày")
            break
            
        # 2. Lấy thông tin cơ bản
        profile_link = str(row.get('Link', '')).strip()
        name = str(row.get('Name', '')).strip()
        message = str(row.get('Message', '')).strip()
        current_status = str(row.get('Status', '')).strip()

        #Nếu Status là MESSAGE_SENT thì bỏ qua dòng đó
        if current_status == "MESSAGE_SENT":
            print(f"SKIP: Dòng {index+2} ({name}) đã gửi thành công trước đó.")
            send_count += 1
            continue

        # Kiểm tra nếu thiếu Name, Link hoặc Message thì bỏ qua
        if pd.isna(profile_link) or profile_link == "" or pd.isna(message) or message == "":
            print(f"SKIP: Dòng {index+2} thiếu thông tin.")
            df.at[index, 'Status'] = "ERROR: MISSING DATA"
            continue

        # Kiểm tra nếu trùng link đã gửi trong PHIÊN NÀY
        if profile_link in sent_links:
            print(f"SKIP: Link trùng lặp tại dòng {index+2}: {profile_link}")
            df.at[index, 'Status'] = "ERROR: DUPLICATE LINK"
            continue

        print(f"Processing: {profile_link}")
        
        # datum = check_datum(row)
        # if isinstance(datum, str):
        #     status = datum
                    
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                driver.get(profile_link)
                random_delay(5, 10) 
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                
                result = send_message_optimized(driver, row)
                status = "MESSAGE_SENT" if result == "SUCCESS" else (f"MESSAGE_{result}" if result == "UNKNOWN" else result)

                if result == "SUCCESS":
                    send_count += 1
                    sent_links.add(profile_link)
                    print(f"-> Gửi thành công đến {profile_link} | Lần {attempt}: {send_count}/{MAX_MESSAGES_PER_DAY}")
                    break 
                
                print(f"-> Thử lại lần {attempt} do lỗi: {result}")

            except Exception as e:
                status = f"ERROR: {str(e)}"
                print(f"-> Lỗi Exception lần {attempt}: {e}")
            
            # Chỉ delay nếu chưa phải lần thử cuối cùng
            if attempt < MAX_RETRIES:
                random_delay(5, 8)
        else:
            # Vòng lặp chạy hết mà không break (không SUCCESS)
            status = status if "ERROR" in status else "ERROR: FAILED AFTER RETRIES"

        # Cập nhật trạng thái vào DataFrame
        df.at[index, 'Status'] = status
        
        # Nghỉ giữa các profile khác nhau
        if status == "MESSAGE_SENT":
            random_delay(15, 25)
        else:
            random_delay(5, 10)
    # else:
    #     print("CRITICAL: Không thể tiến hành gửi tin nhắn vì đăng nhập thất bại.")
    #CẬP NHẬT TRẠNG THÁI LÊN GOOGLE SHEETS.
    try:
        status_list = df[['Status']].values.tolist()
        start_row = 2
        end_row = start_row + len(status_list) - 1
        status_range = f"C{start_row}:C{end_row}"
        #updated_values = [df.columns.tolist()] + df.values.tolist()
        #sheet.update(RANGE_NAME, updated_values)
        sheet.update(status_range, status_list)
        print("\nINFO: Đã cập nhật trạng thái lên Google Sheets.")
    except Exception as e:
        print(f"CRITICAL ERROR: Không thể cập nhật Google Sheets: {e}")
    
    """# **KẾT THÚC CHƯƠNG TRÌNH**"""
    driver.quit()
    print("ĐÃ THOÁT")
