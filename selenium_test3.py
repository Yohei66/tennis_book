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
from selenium.common.exceptions import NoAlertPresentException

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
import calendar
import time
import re
import jpholiday 

# 今日の日付を取得
today = datetime.today()

# 3か月後の日付を計算
three_months_later = today + relativedelta(months=3)

# 年、月、日に分解
year = three_months_later.year
month = three_months_later.month
day = three_months_later.day

id="52003401"

password="1234"

places={'大沼公園グラウンド','立沼テニス場'}

weekdays={'火','水','木','金','土','日','祝'}


# WebDriverのオプションを設定
options = Options()

# サービスを設定
service = Service('C:/chromedriver-win64/chromedriver.exe')

# WebDriverを初期化
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://www.pf489.com/kasukabe/web/Wg_ModeSelect.aspx")
driver.maximize_window()
driver.find_element(By.ID, "rbtnLogin").click()
driver.find_element(By.ID, "txtID").click()
driver.find_element(By.ID, "txtID").send_keys(id)
driver.find_element(By.ID, "txtPass").click()
driver.find_element(By.ID, "txtPass").send_keys(password)
driver.find_element(By.ID, "ucPCFooter_btnForward").click()

try:
    WebDriverWait(driver, 10).until(EC.alert_is_present())
    alert = driver.switch_to.alert
    alert.accept()
except NoAlertPresentException:
    print("アラートが存在しません")
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

def get_facility_element():
    facility_xpath = "//span[contains(@id, '_lblShisetsu') and text()='大沼公園グラウンド']/ancestor::table[contains(@id, '_tpItem')]"
    return driver.find_element(By.XPATH, facility_xpath)

def get_dg_table(facility_element):
    return facility_element.find_element(By.XPATH, ".//table[contains(@id, '_dgTable')]")

def get_displayed_month(dg_table):
    month_cell = dg_table.find_element(By.XPATH, ".//tr[1]/td[1]")
    month_text = month_cell.text  # 例："2024年10月"
    match = re.search(r'(\d+)年(\d+)月', month_text)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        return year, month
    else:
        return None, None

def get_next_month_link(facility_element):
    return facility_element.find_element(By.XPATH, ".//a[contains(@id, 'Migrated_lnkNextSpan')]")

def get_prev_month_link(facility_element):
    return facility_element.find_element(By.XPATH, ".//a[contains(@id, 'Migrated_lnkPrevSpan')]")

# 現在の年月を取得
today = datetime.today()
current_year = today.year
current_month = today.month

# 月の日数を取得
num_days = calendar.monthrange(current_year, current_month)[1]

# 木土日祝の日時を取得
dates_to_click = []
for day in range(1, num_days + 1):
    date = datetime(current_year, current_month, day)
    weekday = date.weekday()  # 月曜日=0, 日曜日=6
    if weekday in [3, 5, 6] or jpholiday.is_holiday(date):
        dates_to_click.append(date)

# 施設要素を取得
facility_element = get_facility_element()
dg_table = get_dg_table(facility_element)

# 必要な月にナビゲート
max_attempts = 12  # 無限ループ防止のため
attempts = 0

while attempts < max_attempts:
    displayed_year, displayed_month = get_displayed_month(dg_table)
    if displayed_year == current_year and displayed_month == current_month:
        break
    elif (displayed_year, displayed_month) < (current_year, current_month):
        next_month_link = get_next_month_link(facility_element)
        next_month_link.click()
        time.sleep(1)
        facility_element = get_facility_element()
        dg_table = get_dg_table(facility_element)
    else:
        prev_month_link = get_prev_month_link(facility_element)
        prev_month_link.click()
        time.sleep(1)
        facility_element = get_facility_element()
        dg_table = get_dg_table(facility_element)
    attempts += 1

if attempts >= max_attempts:
    print("目的の月に移動できませんでした。")
else:
    for date in dates_to_click:
        date_str = date.strftime('%Y%m%d')
        date_id = '_b' + date_str
        try:
            date_element = dg_table.find_element(By.XPATH, f".//a[contains(@id, '{date_id}')]")
            date_element.click()
            time.sleep(0.5)  # 必要に応じて調整
        except NoSuchElementException:
            print(f"{date_str} の要素が見つかりませんでした。")

while True:
    pass