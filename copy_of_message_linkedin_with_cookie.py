
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from IPython.display import Image, display
from oauth2client.service_account import ServiceAccountCredentials
from fastapi import FastAPI
import pandas as pd
import gspread

"""# **HÀM HỖ TRỢ**"""

def display_screenshot(driver: webdriver.Chrome, file_name: str = 'screenshot.png'):
    driver.save_screenshot(file_name)
    time.sleep(5)
    display(Image(filename=file_name))


def capture_full_page_screenshot(driver: webdriver.Chrome, file_name: str = 'full_screenshot.png'):
    # Cấu hình lại kích thước cửa sổ để chụp toàn màn hình
    total_width = driver.execute_script("return document.body.scrollWidth")
    total_height = driver.execute_script("return document.body.scrollHeight")
    driver.set_window_size(total_width, total_height)

    # Chụp ảnh màn hình với kích thước đã cấu hình
    driver.save_screenshot(file_name)

    # Hiển thị ảnh đã chụp
    time.sleep(2)
    display(Image(filename=file_name))

"""# **KẾT NỐI GOOGLE SHEETS**"""



# Thông tin bảng tính
SPREADSHEET_ID = os.getenv('SPREADSHEET_MESS_ID')
SHEET_NAME = 'Sheet1'
RANGE_NAME = 'A:E'
KEYFILE_PATH = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Xác thực với Google Sheets API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(KEYFILE_PATH, scope)
client = gspread.authorize(creds)

# Lấy dữ liệu từ bảng tính
sheet = client.open_by_key(SPREADSHEET_ID).worksheet('Sheet1')
values = sheet.get_all_values()
df = pd.DataFrame(values[1:], columns=values[0])

print(df)

"""# **HIỂN THỊ THÔNG TIN GOOGLE SHEETS**"""

df.head()

"""# **CẤU HÌNH DRIVER**"""

options = webdriver.ChromeOptions()

options.add_argument('--no-sandbox')
options.add_argument("--disable-dev-shm-usage")
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument("--window-size=1920, 1200")
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

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
        code = input("Verification code required! Check your email and enter the code: ")
        verification_field.send_keys(code)
        time.sleep(1)
        submit_button.click()
        time.sleep(2)
    except:
        print("INFO: NO VERIFICATION DETECTED!")

def login(driver: webdriver.Chrome, username, password):
    try:
        driver.get("https://www.linkedin.com/login")
        # display_screenshot(driver)
        capture_full_page_screenshot(driver)
        # WAIT FOR LOADING PAGE.
        XPATH_USERNAME, XPATH_PASSWORD = '//*[@id="username"]', '//*[@id="password"]'
        username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, XPATH_USERNAME)))
        password_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, XPATH_PASSWORD)))
        login_button = driver.find_element(By.XPATH, "//button[normalize-space(text())='Sign in']")
        # ENTER USERNAME.
        username_field.send_keys(username)
        time.sleep(2)
        # ENTER PASSWORD.
        password_field.send_keys(password)
        time.sleep(2)
        # CLICK LOGIN BUTTON.
        login_button.click()
    except TimeoutException:
        raise Exception("ERROR: ELEMENT NOT FOUND!")
    except:
        raise Exception("ERROR: LOGIN FAILED!")
    # CHECK VERIFY.
    handle_code_verification(driver)
    handle_cookie_acceptance(driver)
    time.sleep(5)
    display_screenshot(driver)

"""# **THỰC HIỆN ĐĂNG NHẬP**"""

username = os.getenv("LINKEDIN_MESS_USERNAME")
password = os.getenv("LINKEDIN_MESS_PASSWORD")

login(driver, username, password)

"""# **XPATH**"""

# XPATH ỨNG VỚI NÚT MESSAGE.
#BUTTON_MESSAGE = "/html/body/div[5]/div[3]/div/div/div[2]/div/div/main/section[1]/div[2]/div[3]/div/div[1]/button"
BUTTON_MESSAGE = "/html/body/div[6]/div[3]/div/div/div[2]/div/div/main/section[1]/div[2]/div[3]/div/div[1]/button"
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
    # KIỂM TRA TỆP ĐÍNH KÈM.
    attachment = datum["Attachment"]
    # !wget https://github.com/TAHKInteractingAI/Automatic_Colab/blob/main/HenryUniversesResume.pdf
    # !wget https://github.com/TAHKInteractingAI/Automatic_Colab/blob/main/tokyo-vigil-436805-j9-d6e61a754dce.json

    url = '/content/' + attachment
    print(url)
    if attachment:
        rel_path = os.path.join(attachment)
        abs_path = os.path.abspath(rel_path)
        if not os.path.exists(abs_path):
            print("ERROR: ATTACHMENT NOT FOUND!")
            return "ERROR: ATTACHMENT NOT FOUND"
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
            display_screenshot(driver)
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

"""# **THỰC HIỆN GỬI TIN NHẮN**"""

# DUYỆT QUA TỪNG PROFILE VÀ GỬI TIN NHẮN.
def main_mess():
    for index, row in df.iterrows():
        profile_link = row['Link']
        print(profile_link, end=" ")
        # KIỂM TRA DỮ LIỆU.
        datum = check_datum(row)
        if isinstance(datum, str):
            status = datum
        else:
            driver.get(profile_link)
            # GỬI TIN NHẮN.
            status = send_message(driver, profile_link, datum)
            # capture_full_page_screenshot(driver)
            display_screenshot(driver)
        # LƯU TRẠNG THÁI.
        df.at[index, 'Status'] = status
    # CẬP NHẬT TRẠNG THÁI LÊN GOOGLE SHEETS.
    updated_values = [df.columns.tolist()] + df.values.tolist()
    sheet.update(RANGE_NAME, updated_values)


"""# **KẾT THÚC CHƯƠNG TRÌNH**"""

