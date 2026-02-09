
import json
import os
import time
import base64
import random, pickle
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
#from IPython.display import Image, display
from oauth2client.service_account import ServiceAccountCredentials
from fastapi import FastAPI
import requests
import re
import pandas as pd
from dotenv import load_dotenv
import gspread
from pathlib import Path

load_dotenv()

"""# **CONFIG**"""
MISSIVE_API_KEY = os.getenv('MISSIVE_API_KEY')
MAX_MESSAGES_PER_DAY = 15
COOKIES_FILE = 'linkedin_cookies.pkl'
headers = {"Authorization": f"Bearer {MISSIVE_API_KEY}", "Content-Type": "application/json"}
params = {"limmit": 20, "inbox":"true"} 
# Thông tin bảng tính
SPREADSHEET_ID = os.getenv('SPREADSHEET_MESS_ID')
SHEET_NAME = 'Sheet1'
RANGE_NAME = 'A:E'
GOOGLE_CREDS = os.getenv('GOOGLE_APPLICATION_CRED')

"""# **HÀM HỖ TRỢ**"""
def get_missive_linkedin_code():
    
    response = requests.get("https://public.missiveapp.com/v1/conversations", headers=headers, params=params)
    if response.status_code != 200:
        return f"Lỗi API: {response.status_code}"
    conversations = response.json().get("conversations", [])
    temp = [c for c in conversations if 'name' in c['authors'][0] and c['authors'][0]['name'] == 'LinkedIn']
    return temp[0]['latest_message_subject'].split(' ')[-1:][0]

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
def get_data_with_links(sheet):
    # 1. Lấy toàn bộ giá trị của bảng tính (để biết chính xác số dòng hiện có)
    all_values = sheet.get_all_values()
    if len(all_values) < 2:
        return pd.DataFrame()

    headers = all_values[1]  # Dòng 2 (index 1) là header
    data_rows = all_values[2:] # Dữ liệu thực tế từ dòng 3
    num_rows = len(data_rows)

    # 2. Lấy metadata của cột E (Attachment) - Giả sử là cột số 5
    # Chỉ lấy đúng phạm vi tương ứng với số dòng dữ liệu đang có
    spreadsheet = sheet.spreadsheet
    sheet_name = sheet.title
    range_metadata = f"{sheet_name}!E3:E{2 + num_rows}"
    
    res_metadata = spreadsheet.fetch_sheet_metadata({
        'includeGridData': True,
        'ranges': [range_metadata]
    })
    
    links_per_row = []
    # Truy cập vào cấu trúc dữ liệu JSON của Google
    sheets_data = res_metadata.get('sheets', [])[0].get('data', [])[0]
    rowData = sheets_data.get('rowData', [])
    
    for row in rowData:
        cell_links = []
        values = row.get('values', [])
        if values:
            cell = values[0]
            # Ưu tiên 1: Link bao trùm toàn bộ ô
            if 'hyperlink' in cell:
                cell_links.append(cell['hyperlink'])
            # Ưu tiên 2: Nhiều link trong các đoạn văn bản (Rich Text)
            elif 'textFormatRuns' in cell:
                for run in cell['textFormatRuns']:
                    url = run.get('format', {}).get('link', {}).get('uri')
                    if url:
                        cell_links.append(url)
        
        # Gộp các link, loại bỏ trùng lặp bằng set
        unique_links = list(dict.fromkeys(cell_links))
        links_per_row.append(", ".join(unique_links))

    # 3. Đảm bảo links_per_row có độ dài bằng với data_rows
    # Nếu metadata trả về thiếu, bù cho đủ bằng chuỗi rỗng
    while len(links_per_row) < num_rows:
        links_per_row.append("")

    # 4. Tạo DataFrame
    df = pd.DataFrame(data_rows, columns=headers)
    
    # Cập nhật cột Attachment (cần chắc chắn tên cột đúng 100% với file Sheets)
    if 'Attachment' in df.columns:
        df['Attachment'] = links_per_row[:num_rows]
    
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
def get_driver():
    options = webdriver.ChromeOptions()
    
    # 1. Định nghĩa một User-Agent nhất quán (Tránh khai báo 2 lần)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"user-agent={user_agent}")

    # 2. Các thiết lập cơ bản cho môi trường Linux/Docker (GitHub Actions)
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--disable-gpu')
    options.add_argument('--headless=new')
    options.add_argument("--window-size=1920,1200")
    
    # 3. CHỐNG PHÁT HIỆN BOT (Stealth Mode)
    # Loại bỏ cờ 'nút điều khiển tự động'
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # Vô hiệu hóa tính năng AutomationControlled của Blink
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Thêm các cờ để trình duyệt giống người dùng thật hơn
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    
    # Khởi tạo driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # 4. Ẩn thuộc tính navigator.webdriver bằng Script thực thi ngay khi load trang
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    
    return driver

"""# **HÀM ĐĂNG NHẬP**"""
                
def handle_cookie_acceptance(driver: webdriver.Chrome):
    try:
        driver.find_element(By.XPATH, "//button[span[text()='Accept']]").click()
        print("INFO: COOKIES IS ACCEPTED!")
    except:
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
        print(code)
        driver.save_screenshot("before_verification.png")
        time.sleep(2)
        verification_field.send_keys(code)
        time.sleep(3)
        submit_button.click()
        time.sleep(5)
    except:
        print("INFO: NO VERIFICATION DETECTED!")

def login(driver: webdriver.Chrome, username: str, password: str):
    """Đăng nhập vào LinkedIn với username và password mới nếu có sự thay đổi"""
    XPATH_USERNAME = '//*[@id="username"]'
    XPATH_PASSWORD = '//*[@id="password"]'
    XPATH_LOGIN_BUTTON = '//button[contains(@class, "btn__primary--large") and @aria-label="Sign in"]'

    driver.get("https://www.linkedin.com/login")
    time.sleep(2)  # Ensure the page is fully loaded

    # Kiểm tra nếu có cookies và kiểm tra xem username, password có thay đổi không
    #credentials = load_credentials()

    if os.path.exists(COOKIES_FILE):# and credentials:
        # Kiểm tra nếu username hoặc password đã thay đổi
        #if credentials['username'] == username and credentials['password'] == password:
            # Tải cookies và thử đăng nhập
        load_cookies(driver, COOKIES_FILE)
        driver.get("https://www.linkedin.com/feed")
        time.sleep(3)

        # Kiểm tra xem đã đăng nhập chưa bằng cách xem có biểu tượng người dùng không
        try:
            user_icon = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'global-nav__me-photo')))
            print("INFO: Logged in using cookies!")
            driver.save_screenshot("cookie-login.png")
            # save user_icon
            #user_icon.screenshot("user_icon.png")
            # display_screenshot(driver, "status.png")
            return
        except:
            print("INFO: Cookies không hợp lệ, thử đăng nhập lại...")

    # Nếu thông tin đăng nhập đã thay đổi hoặc không có cookies, đăng nhập thủ công
    driver.get("https://www.linkedin.com/login")
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
    handle_code_verification(driver)
    handle_cookie_acceptance(driver)
    # Lưu cookies và thông tin đăng nhập sau khi đăng nhập thành công
    save_cookies(driver)
    #save_credentials(username, password)
    print("INFO: Đăng nhập thành công và đã lưu cookies, thông tin đăng nhập!")
    driver.save_screenshot("post-login.png")
    # user_icon = WebDriverWait(driver, 10).until(
    #                 EC.presence_of_element_located((By.CLASS_NAME, 'global-nav__me-photo')))
    # # save user_icon
    # user_icon.screenshot("user_icon.png")
    # display_screenshot(driver, "status.png")
    # display_full_screenshot(driver)

def login_with_cookie(driver):
    """Xử lý đăng nhập bằng Cookie li_at từ .env"""
    print("INFO: Đang thử đăng nhập bằng Cookie...")
    # Bước 1: Vào domain LinkedIn trước để trình duyệt chấp nhận cookie
    driver.get("https://www.linkedin.com/login")
    time.sleep(3)

    li_at_cookie = os.getenv("LINKEDIN_COOKIE")
    
    if li_at_cookie:
        try:
            driver.delete_all_cookies()
            driver.add_cookie({
                "name": "li_at",
                "value": li_at_cookie,
                "domain": ".linkedin.com",
                "path": "/",
                "secure": True
            })
            
            # Bước 2: Refresh vào trang Feed
            driver.get("https://www.linkedin.com/feed/")
            time.sleep(5)
            
            # Bước 3: Kiểm tra xem đã vào được Feed chưa (tránh trường hợp cookie hết hạn)
            if "feed" in driver.current_url.lower():
                print(f"SUCCESS: Đăng nhập Cookie thành công! Tiêu đề: {driver.current_url.lower()}")
                return True
            else:
                print("WARNING: Cookie không hiệu lực (có thể đã hết hạn).")
                return False
        except Exception as e:
            print(f"ERROR: Lỗi khi add cookie: {e}")
            return False
    else:
        print("ERROR: Không tìm thấy biến môi trường LINKEDIN_COOKIE")
        return False
        

"""# **XPATH**"""

# XPATH ỨNG VỚI NÚT MESSAGE.
#BUTTON_MESSAGE = "/html/body/div[5]/div[3]/div/div/div[2]/div/div/main/section[1]/div[2]/div[3]/div/div[1]/button"
#BUTTON_MESSAGE = "/html/body/div[6]/div[3]/div/div/div[2]/div/div/main/section[1]/div[2]/div[3]/div/div[1]/button"
BUTTON_MESSAGE = "/html/body/div/div[2]/div[2]/div[2]/div/main/div/div/div[1]/div/div/div[1]/div/section/div/div/div[2]/div[3]/div/div/div/a"
# XPATH ỨNG VỚI KHUNG TIN NHẮN. (CLASS NAME)
FIELD_MESSAGE = "msg-form__contenteditable"
# XPATH ỨNG VỚI KHUNG ĐÍNH KÈM TỆP. (CLASS NAME)
FIELD_ATTACHMENT = "msg-form__attachment-upload-input"
# XPATH ỨNG VỚI NÚT GỬI TIN NHẮN. (CLASS NAME)
BUTTON_SUBMIT_MESSAGE = "msg-form__send-button"
#BUTTON_SUBMIT_MESSAGE = "/html/body/div[5]/div[4]/aside[1]/div[2]/div[1]/div[2]/div/form/footer/div[2]/div[1]/button"
# XPATH ỨNG VỚI NÚT ĐÓNG HỘP THOẠI NHẮN TIN.
#BUTTON_CLOSE_MESSAGE = "/html/body/div[5]/div[4]/aside[1]/div[2]/div[1]/header/div[4]/button[3]"
BUTTON_CLOSE_MESSAGE = "/html/body/div[6]/div[4]/aside[1]/div[2]/div[1]/header/div[4]/button[3]"

# XPATH cập nhật (LinkedIn thường xuyên đổi ID nên dùng Class hoặc Text ổn định hơn)
FIELD_MESSAGE_CLASS = "msg-form__contenteditable"
BUTTON_SEND_CLASS = "msg-form__send-button"

"""# **HÀM GỬI TIN NHẮN**"""
def check_datum(datum):
    # KIỂM TRA TÊN.
    name = datum["Name"]
    if not name:
        print("ERROR: NAME NOT FOUND!")
        return "ERROR: NAME NOT FOUND!"
    # KIỂM TRA TIN NHẮN.
    message = datum["Message"]
    if not message:
        print("ERROR: MESSAGE NOT FOUND!")
        return "ERROR: MESSAGE NOT FOUND!"
    # KIỂM TRA TỆP ĐÍNH KÈM. (XỮ LÍ ĐA NỀN TẢNG)
    #attachment = datum["Attachment"]
    # !wget https://github.com/InteractingAI/Automatic_Colab/blob/main/HenryUniversesResume.pdf
    # !wget https://github.com/InteractingAI/Automatic_Colab/blob/main/tokyo-vigil-436805-j9-d6e61a754dce.json
    attachment_name = datum.get("Attachment")
    abs_path = None
    if attachment_name and str(attachment_name).strip():
        # Lấy thư mục gốc nơi script đang chạy (tương thích cả Local và Server)
        # Nếu chạy trên GitHub Actions, nó sẽ là thư mục repo
        base_path = Path(__file__).parent.absolute()
        file_path = base_path / attachment_name
        
        if file_path.exists():
            abs_path = str(file_path)
            print(f"INFO: Attachment found at: {abs_path}")
        else:
            print(f"WARNING: File {attachment_name} không tồn tại tại {base_path}. Sẽ gửi tin không đính kèm.")
    
    # url = '/content/' + attachment
    # print(url)
    # if attachment:
    #     rel_path = os.path.join(attachment)
    #     abs_path = os.path.abspath(rel_path)
    #     if not os.path.exists(abs_path):
    #         print("ERROR: ATTACHMENT NOT FOUND!")
    #         return "ERROR: ATTACHMENT NOT FOUND"
    # XỬ LÝ TIN NHẮN.
    message = message.replace("{{Name}}", name)

    return name, message, abs_path

def send_message(driver: webdriver.Chrome, target_profile, datum):
    name, message, attachment = datum

    try:
        # TÌM KIẾM NÚT MỞ HỘP THOẠI TIN NHẮN.
        c = EC.presence_of_element_located((By.XPATH, BUTTON_MESSAGE))
        # capture_full_page_screenshot(driver)
        try:
            e = WebDriverWait(driver, 15).until(c)
        except:
            print("ERROR: OPEN BUTTON NOT FOUND!")
            return "ERROR: OPEN BUTTON NOT FOUND!"
        # KIỂM TRA NÚT CÓ PHẢI LÀ NÚT MỞ HỘP THOẠI TIN NHẮN.
        status = e.get_attribute("aria-label")
        if "Message" not in status:
            print("ERROR: BUTTON IS NOT MESSAGE BUTTON!")
            return "ERROR: BUTTON IS NOT MESSAGE BUTTON!"
        # NHẤN NÚT.
        e.click()
        time.sleep(2)
        # capture_full_page_screenshot(driver)
        # TÌM KIẾM KHUNG TIN NHẮN.
        try:
            e = driver.find_element(By.CLASS_NAME, FIELD_MESSAGE)
            # capture_full_page_screenshot(driver)
        except NoSuchElementException:
            print("ERROR: MESSAGE BOX NOT FOUND!")
            return "ERROR: MESSAGE BOX NOT FOUND!"
        # XÓA TIN NHẮN MẶC ĐỊNH.
        if e.text != "":
            e.send_keys(Keys.CONTROL + "a")
            e.send_keys(Keys.DELETE)
            time.sleep(2)
        # NHẬP TIN NHẮN.
        e.send_keys(message)
        time.sleep(2)
        # capture_full_page_screenshot(driver)
        if attachment:
            # TÌM KIẾM KHUNG ĐÍNH KÈM.
            try:
                e = driver.find_element(By.CLASS_NAME, FIELD_ATTACHMENT)
            except NoSuchElementException:
                print("ERROR: ATTACHMENT BOX NOT FOUND!")
                return "ERROR: ATTACHMENT BOX NOT FOUND!"
            # ĐÍNH KÈM TỆP.
            e.send_keys(attachment)
            # capture_full_page_screenshot(driver)
            #display_screenshot(driver)
            time.sleep(2)

        # TÌM KIẾM NÚT GỬI TIN NHẮN.
        c = EC.presence_of_element_located((By.CLASS_NAME, BUTTON_SUBMIT_MESSAGE))
        try:
            e = WebDriverWait(driver, 15).until(c)
            driver.execute_script("arguments[0].click();", e)
            # capture_full_page_screenshot(driver)
        except:
            print("ERROR: SUBMIT BUTTON NOT FOUND!")
            return "ERROR: SUBMIT BUTTON NOT FOUND!"
        # NHẤN NÚT
        time.sleep(2)

        # TÌM KIẾM NÚT ĐÓNG HỘP THOẠI.
        # c = EC.presence_of_element_located((By.XPATH, BUTTON_CLOSE_MESSAGE))
        # try:
        #     e = WebDriverWait(driver, 15).until(c)
        #     display_screenshot(driver)
        # except:
        #     print("ERROR: CLOSE BUTTON NOT FOUND!")
        #     return "ERROR: CLOSE BUTTON NOT FOUND!"
        # # NHẤN NÚT.
        # e.click()
        # display_screenshot(driver)
        # time.sleep(2)

        return "MESSAGE HAS SENT!"
    except Exception as e:
        print("\n" + str(e))
        return "ERROR: MESSAGE NOT SENT!"

def send_message_optimized(driver, row):
    try:
        name = row['Name']
        message_template = row['Message'].replace("{{Name}}", name)
        attachment = str(row.get('Attachment', "")).strip()
        if attachment and attachment.lower() != "nan":
            # Nối link vào cuối tin nhắn theo định dạng rõ ràng
            full_message = f"{message_template}\n\nAttached profile files: {attachment}"
        else:
            full_message = message_template
        #print(full_message)
        # attachment_path = None
        # if row.get('Attachment') and str(row.get('Attachment')).strip()!= "":
        #     attachment_path = os.path.abspath(row['Attachment'])
        # TÌM NÚT MESSAGE
        try:
            msg_btn = WebDriverWait(driver, 10).until(
               EC.element_to_be_clickable((By.XPATH, BUTTON_MESSAGE))
            )
            msg_btn.click()
        except:
            return "ERROR: MESSAGE BUTTON NOT FOUND"
        time.sleep(2)
        print("Message button found, ready to type input")
        # NHẬP NỘI DUNG
        # msg_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, FIELD_MESSAGE_CLASS)))
        #print("Message box found")
        #msg_box.click()
        #print("Ready to input")
        #human_type(msg_box, full_message)
        # msg_box.send_keys(full_message)
        #driver.switch_to.active_element.send_keys(full_message)
        actions = ActionChains(driver)
        actions.send_keys(full_message)
        actions.perform()
        print("Message input complete")
        actions.send_keys(Keys.SPACE).perform()
        time.sleep(2)
        #safe_type_multiline(msg_box, full_message)
        #Nhập nội dung dùng JavaScript để hỗ trợ Link dài
        # driver.execute_script("""
        #     var el = arguments[0];
        #     var text = arguments[1];
        #     el.focus();
        #     document.execCommand('insertText', false, text);
        # """, msg_box, full_message)
        #time.sleep(2)
        try:
            # Tìm nút Gửi bằng XPATH linh hoạt (thường ổn định hơn Class)
            send_btn_xpath = "//button[contains(@class, 'msg-form__send-button')] | //button[text()='Send']"
            send_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, send_btn_xpath))
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
    
    # # THỰC HIỆN ĐĂNG NHẬP
    # # Thử bằng cookie trước
    # logged_in = login_with_cookie(driver)
    
    # # Nếu cookie thất bại, thử login bằng username/password
    # if not logged_in:
    #     print("INFO: Chuyển sang đăng nhập bằng Username/Password...")
    #     username = os.getenv("LINKEDIN_USERNAME")
    #     password = os.getenv("LINKEDIN_PASSWORD")
    #     if username and password:
    #         try:
    #             login(driver, username, password)
    #             logged_in = True
    #         except Exception as e:
    #             print(f"CRITICAL: Đăng nhập thủ công thất bại: {e}")
    #     else:
    #         print("CRITICAL: Thiếu thông tin LINKEDIN_USERNAME/PASSWORD trong .env")

    # # Nếu đăng nhập thành công (bằng bất cứ cách nào) thì mới chạy tiếp
    # if logged_in:
    username = os.getenv("LINKEDIN_USERNAME")
    password = os.getenv("LINKEDIN_PASSWORD")
    login(driver, username, password)
    """# **THỰC HIỆN GỬI KẾT NỐI**"""
    send_count = 0
    
    for index, row in df.iterrows():
        if send_count >= MAX_MESSAGES_PER_DAY:
            print(f"INFO: Đã đạt giới hạn {MAX_MESSAGES_PER_DAY} người/ngày")
            break
            
        profile_link = row['Link']
        print(f"Processing: {profile_link}")
        
        datum = check_datum(row)
        if isinstance(datum, str):
            status = datum
        else:
            try:
                driver.get(profile_link)
                random_delay(5, 10) # Tránh bị LinkedIn quét bot
                
                status = send_message_optimized(driver, row)
                
                if status == "SUCCESS":
                    send_count += 1
                    status = "MESSAGE_SENT"
                    print(f"-> Gửi thành công đến {row['Name']} ({send_count}/{MAX_MESSAGES_PER_DAY})")
                
            except Exception as e:
                status = f"ERROR: {str(e)}"
                print(status)

        # Cập nhật trạng thái vào DataFrame
        df.at[index, 'Status'] = status
        
        # Nghỉ giữa các lần gửi để tránh bị khóa account
        if send_count < MAX_MESSAGES_PER_DAY:
            random_delay(15, 25)
    
    # else:
    #     print("CRITICAL: Không thể tiến hành gửi tin nhắn vì đăng nhập thất bại.")
    #CẬP NHẬT TRẠNG THÁI LÊN GOOGLE SHEETS.
    try:
        status_list = df[['Status']].values.tolist()
        start_row = 3
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

