from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException

import time



# 今日の日付を取得
today = datetime.today()

# 3か月後の日付を計算
three_months_later = today + relativedelta(months=3)

# 年、月、日に分解
year = three_months_later.year
month = three_months_later.month
day = three_months_later.day



places={'大沼公園グラウンド','立沼テニス場'}

weekdays={'月','火','水','木','金','土','日','祝'}


# WebDriverのオプションを設定
options = Options()

# サービスを設定
service = Service('C:/chromedriver-win32/chromedriver.exe')

# WebDriverを初期化
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://www.pf489.com/kasukabe/web/Wg_ModeSelect.aspx")
driver.maximize_window()
driver.find_element(By.ID, "rbtnLogin").click()
driver.find_element(By.ID, "txtID").click()
driver.find_element(By.ID, "txtID").send_keys("52003400")
driver.find_element(By.ID, "txtPass").click()
driver.find_element(By.ID, "txtPass").send_keys("1234")
driver.find_element(By.ID, "ucPCFooter_btnForward").click()
alert = driver.switch_to.alert
alert.accept()
driver.find_element(By.ID, "btnNormal").click()
driver.find_element(By.ID, "rbtnYoyaku").click()
driver.find_element(By.ID, "btnMokuteki").click()
driver.find_element(By.ID, "ucOecRadioButtonList_dgButtonList_ctl02_rdSelectLeft").click()
driver.find_element(By.ID, "ucButtonList_dgButtonList_ctl03_chkSelectRight").click()
driver.find_element(By.ID, "ucPCFooter_btnForward").click()
driver.find_element(By.ID, "ucPCFooter_btnForward").click()


for place in places:
    element = driver.find_element(By.XPATH, "//input[@value='"+place+"']")
    element.click()

driver.find_element(By.ID, "ucPCFooter_btnForward").click()

driver.find_element(By.ID, "txtYear").send_keys(Keys.CONTROL+"a")
driver.find_element(By.ID, "txtYear").send_keys(Keys.DELETE)
driver.find_element(By.ID, "txtYear").send_keys(year)
driver.find_element(By.ID, "txtMonth").send_keys(Keys.CONTROL+"a")
driver.find_element(By.ID, "txtMonth").send_keys(Keys.DELETE)
driver.find_element(By.ID, "txtMonth").send_keys(month)
driver.find_element(By.ID, "txtDay").send_keys(Keys.CONTROL+"a")
driver.find_element(By.ID, "txtDay").send_keys(Keys.DELETE)
driver.find_element(By.ID, "txtDay").send_keys("1")

driver.find_element(By.ID,"rbtnMonth").click()


# Table6の中のtbodyの中のtrの中のtdの中のinputの中の値＝曜日
for weekday in weekdays:
        driver.find_element(By.XPATH, "//table[@id='Table6']/tbody/tr/td/input[@value='"+weekday+"']").click()
driver.find_element(By.ID, "ucPCFooter_btnForward").click()

# driver.find_element(By.ID, "dgTable_ctl02_chkShisetsu").click()
# driver.find_element(By.ID, "dgTable_ctl03_chkShisetsu").click()
# driverWebDriverWait(driver, 10)
# try:
#     # Adjust the XPath to locate the specific button for 共用B on Tuesdays 17:00-19:00
#     button = wait.until(EC.element_to_be_clickable((By.XPATH, '//td[contains(text(), "17:00～19:00")]/following-sibling::td[contains(text(), "共用B")]/preceding-sibling::td/input[@type="submit"]')))
#     button.click()
#     print("Button clicked successfully!")
# except Exception as e:
#     print(f"An error occurred: {e}")


wait = WebDriverWait(driver, 10)

# 大沼公園のテーブルを見つける


# 1. 大沼公園グラウンドを含むテーブルを見つける
# driver.find_element(By.XPATH,"//body[1]/form[1]/table[1]/tbody[1]/tr[2]/td[1]/table[1]/tbody[1]/tr[1]/td[2]/table[1]/tbody[1]/tr[1]/td[1]/div[1]/table[4]/tbody[1]/tr[1]/td[1]/table[1]/tbody[1]/tr[1]/td[1]/font[1]/table[1]/tbody[1]/tr[2]/td[1]/table[1]/tbody[1]/tr[2]/td[3]").click()

# リトライ回数の設定
RETRY_COUNT = 3


def find_tuesday_elements(table):
    for attempt in range(RETRY_COUNT):
        try:
            # 火曜日の列を取得 (この例では3列目が火曜日と仮定)
            tuesday_elements = table.find_elements(By.XPATH, ".//tr/td[position() mod 7 = 3]")
            return tuesday_elements
        except StaleElementReferenceException:
            print(f"Retrying... ({attempt + 1}/{RETRY_COUNT})")
            time.sleep(1)  # 少し待つ
    raise Exception("Failed to retrieve elements after several attempts")

# 大沼公園グラウンドのテーブルを取得
tables = driver.find_elements(By.XPATH, "//span[text()='大沼公園グラウンド' or text()='立沼テニス場']/ancestor::table")
print('---tables---')
print(tables)
print('---tables---')

# 各テーブル内の火曜日要素をクリック
for table in tables:
    print('---table---')
    print(table)
    print('---table---')
    
    tuesday_elements = find_tuesday_elements(table)
    print('---tuesdays---')
    print(tuesday_elements)
    print('---tuesdays---')
    

    for tuesday_element in tuesday_elements:
        clicked = False
        for attempt in range(RETRY_COUNT):
            try:
                ActionChains(driver).move_to_element(tuesday_element).click().perform()
                clicked = True
                print('クリックしました')
                break
            except StaleElementReferenceException as e:
                print(f"StaleElementReferenceException on click attempt {attempt + 1}: {e}")
                tuesday_elements = find_tuesday_elements(table)  # 再取得
                tuesday_element = tuesday_elements[tuesday_elements.index(tuesday_element)]  # 同じインデックスの要素を取得
            except Exception as e:
                print(f"Element not clickable: {e}")
            time.sleep(1)  # 少し待つ
        if not clicked:
            print(f"Failed to click element after several attempts: {tuesday_element}")

while True:
    pass