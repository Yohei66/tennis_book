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
from selenium.common.exceptions import NoAlertPresentException, NoSuchElementException
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

id = "52003401"
password = "1234"

# 施設と対象曜日の設定
facility_days = {
    '大沼公園グラウンド': [3, 5, 6],  # 木、土、日
    '立沼テニス場': [2, 4, 5],  # 水、金、土
}

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

# 施設の選択
for facility_name in facility_days.keys():
    element = driver.find_element(By.XPATH, "//input[@value='" + facility_name + "']")
    element.click()

driver.find_element(By.ID, "ucPCFooter_btnForward").click()

# 日付の入力
driver.find_element(By.ID, "txtYear").send_keys(Keys.CONTROL + "a")
driver.find_element(By.ID, "txtYear").send_keys(Keys.DELETE)
driver.find_element(By.ID, "txtYear").send_keys(year)
driver.find_element(By.ID, "txtMonth").send_keys(Keys.CONTROL + "a")
driver.find_element(By.ID, "txtMonth").send_keys(Keys.DELETE)
driver.find_element(By.ID, "txtMonth").send_keys(month)
driver.find_element(By.ID, "txtDay").send_keys(Keys.CONTROL + "a")
driver.find_element(By.ID, "txtDay").send_keys(Keys.DELETE)
driver.find_element(By.ID, "txtDay").send_keys("1")

driver.find_element(By.ID, "rbtnMonth").click()

# 曜日のチェックボックスは全て選択（施設ごとに処理するため）
all_weekdays = ['月', '火', '水', '木', '金', '土', '日', '祝']
for weekday in all_weekdays:
    checkbox = driver.find_element(By.XPATH, "//table[@id='Table6']/tbody/tr/td/input[@value='" + weekday + "']")
    if checkbox.is_selected():
        continue
    checkbox.click()

driver.find_element(By.ID, "ucPCFooter_btnForward").click()

# 待機オブジェクトを作成
wait = WebDriverWait(driver, 10)

def get_facility_element(facility_name):
    facility_xpath = (
        f"//span[contains(@id, '_lblShisetsu') and contains(text(), '{facility_name}')]/ancestor::table[contains(@id, '_tpItem')]"
        f"|//a[contains(@id, '_lnkShisetsu') and contains(text(), '{facility_name}')]/ancestor::table[contains(@id, '_tpItem')]"
    )
    return wait.until(EC.presence_of_element_located((By.XPATH, facility_xpath)))

def get_dg_table(facility_element):
    return facility_element.find_element(By.XPATH, ".//table[contains(@id, '_dgTable')]")

# ターゲットの年月を設定
current_year = three_months_later.year
current_month = three_months_later.month

# ターゲットの月の日数を取得
num_days = calendar.monthrange(current_year, current_month)[1]

# 各施設ごとに処理
for facility_name, days in facility_days.items():
    try:
        print(f"{facility_name} 開始。")
        # 施設要素を取得
        facility_element = get_facility_element(facility_name)
        print(f"facility_element:{facility_element}")
        dg_table = get_dg_table(facility_element)
        print(f"dg_table:{dg_table}")

        # '大沼公園グラウンド'の場合は祝日を含める
        include_holidays = facility_name == '大沼公園グラウンド'

        # 対象の日付を取得
        dates_to_click = []
        for day in range(1, num_days + 1):
            date = datetime(current_year, current_month, day)
            weekday = date.weekday()
            if weekday in days or (include_holidays and jpholiday.is_holiday(date)):
                dates_to_click.append(date)

        # 対象の日付の要素をクリック
        for date in dates_to_click:
            date_str = date.strftime('%Y%m%d')
            date_id = '_b' + date_str
            try:
                date_element = dg_table.find_element(By.XPATH, f".//a[contains(@id, '{date_id}')]")
                date_element.click()
                time.sleep(0.5)  # 必要に応じて調整
            except NoSuchElementException:
                print(f"{facility_name} の {date_str} の要素が見つかりませんでした。")
        print(f"{facility_name}完了")
    except NoSuchElementException:
        print(f"{facility_name} の施設要素が見つかりませんでした。")
        continue

#次（日付選択画面）に進む 
driver.find_element(By.ID, "ucPCFooter_btnForward").click()

# 以下で日付選択する

while True:
    pass