from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoAlertPresentException,
    NoSuchElementException,
    UnexpectedAlertPresentException,
)
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

# 施設ごとの設定
facility_settings = {
    "大沼公園グラウンド": {
        "木曜日": {"court": "共用Ｂ", "timeslots": ["9:00～11:00", "11:00～13:00"]},
        "金曜日": {"court": "共用Ｂ", "timeslots": ["9:00～11:00", "11:00～13:00"]},
        "土曜日": {"court": "共用Ｂ", "timeslots": ["15:00～17:00"]},
        "日曜日": {"court": "共用Ｂ", "timeslots": ["15:00～17:00"]},
        "祝日": {"court": "共用Ｂ", "timeslots": ["15:00～17:00"]},
    },
    "立沼テニス場": {
        "火曜日": {"court": "硬式Ｂ", "timeslots": ["15:00～17:00"]},
        "水曜日": {"court": "硬式Ｂ", "timeslots": ["15:00～17:00"]},
        "土曜日": {"court": "硬式Ｂ", "timeslots": ["15:00～17:00"]},
        "日曜日": {"court": "硬式Ｂ", "timeslots": ["15:00～17:00"]},
        "祝日": {"court": "硬式Ｂ", "timeslots": ["15:00～17:00"]},
    },
}

# 曜日のマッピングを定義
weekday_map = {
    0: "月曜日",
    1: "火曜日",
    2: "水曜日",
    3: "木曜日",
    4: "金曜日",
    5: "土曜日",
    6: "日曜日",
}

# WebDriverのオプションを設定
options = Options()

# サービスを設定
service = Service("C:/chromedriver-win64/chromedriver.exe")

# WebDriverを初期化
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

driver.get("https://www.pf489.com/kasukabe/web/Wg_ModeSelect.aspx")
driver.maximize_window()
driver.find_element(By.ID, "rbtnLogin").click()
driver.find_element(By.ID, "txtID").click()
driver.find_element(By.ID, "txtID").send_keys(id)
driver.find_element(By.ID, "txtPass").click()
driver.find_element(By.ID, "txtPass").send_keys(password)
driver.find_element(By.ID, "ucPCFooter_btnForward").click()

# アラートの処理
try:
    WebDriverWait(driver, 5).until(EC.alert_is_present())
    alert = driver.switch_to.alert
    alert.accept()
except NoAlertPresentException:
    pass

driver.find_element(By.ID, "btnNormal").click()
driver.find_element(By.ID, "rbtnYoyaku").click()
driver.find_element(By.ID, "btnMokuteki").click()
driver.find_element(
    By.ID, "ucOecRadioButtonList_dgButtonList_ctl02_rdSelectLeft"
).click()
driver.find_element(
    By.ID, "ucButtonList_dgButtonList_ctl03_chkSelectRight"
).click()
driver.find_element(By.ID, "ucPCFooter_btnForward").click()
driver.find_element(By.ID, "ucPCFooter_btnForward").click()

# 施設の選択
for facility_name in facility_settings.keys():
    element = driver.find_element(By.XPATH, f"//input[@value='{facility_name}']")
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
all_weekdays = ["月", "火", "水", "木", "金", "土", "日", "祝"]
for weekday in all_weekdays:
    checkbox = driver.find_element(
        By.XPATH, f"//table[@id='Table6']//input[@value='{weekday}']"
    )
    if not checkbox.is_selected():
        checkbox.click()

# 次（日付選択画面）に進む
driver.find_element(By.ID, "ucPCFooter_btnForward").click()

# 待機オブジェクトを作成
wait = WebDriverWait(driver, 20)

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

# 日付選択画面で、指定の日付を選択
try:
    for facility_name, settings in facility_settings.items():
        try:
            print(f"{facility_name} 開始。")
            # 日付選択画面での施設要素を取得
            facility_element = get_facility_element(facility_name)
            dg_table = get_dg_table(facility_element)

            # 対象の日付を取得
            dates_to_click = []
            num_days = calendar.monthrange(current_year, current_month)[1]
            for day in range(1, num_days + 1):
                date = datetime(current_year, current_month, day)
                weekday = date.weekday()
                weekday_str = weekday_map[weekday]

                # 祝日の判定
                is_holiday = jpholiday.is_holiday(date)
                if is_holiday:
                    weekday_str = "祝日"

                if weekday_str in settings:
                    dates_to_click.append((date, settings[weekday_str]))

            # 対象の日付の要素をクリック
            for date, setting in dates_to_click:
                date_str = date.strftime("%Y%m%d")
                date_id = f"b{date_str}"
                try:
                    date_element = dg_table.find_element(
                        By.XPATH, f".//a[contains(@id, '{date_id}')]"
                    )
                    date_element.click()
                    time.sleep(0.5)  # 必要に応じて調整
                    print(f"{facility_name} の {date.strftime('%Y/%m/%d')} を選択しました。")
                except NoSuchElementException:
                    print(f"{facility_name} の {date.strftime('%Y/%m/%d')} の要素が見つかりませんでした。")
                    continue

            print(f"{facility_name}完了")
        except NoSuchElementException:
            print(f"{facility_name} の施設要素が見つかりませんでした。")
            continue

    # 日付選択後、次のページへ進む
    driver.find_element(By.ID, "ucPCFooter_btnForward").click()

    # コートと時間帯の選択
    print("コートと時間帯の選択開始。")
    # 全ての date_tables を取得
    date_tables = driver.find_elements(By.XPATH, "//table[contains(@id, '_dgTable')]")
    print(f"date_tablesの数: {len(date_tables)}")

    for dg_table_date in date_tables:
        # 施設名を取得
        try:
            facility_name_element = dg_table_date.find_element(
                By.XPATH, "./preceding::*[contains(@id, '_lblShisetsu') or contains(@id, '_lnkShisetsu')][1]"
            )

            facility_name_text = facility_name_element.text.strip()
        except NoSuchElementException:
            continue

        if facility_name_text not in facility_settings:
            continue

        settings = facility_settings[facility_name_text]

        # 日付を取得
        date_text = dg_table_date.find_element(By.XPATH, ".//tr[1]/td[1]").text
        date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", date_text)
        if date_match:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            date = datetime(year, month, day)
            date_str = date.strftime("%Y/%m/%d")
            weekday = date.weekday()
            weekday_str = weekday_map[weekday]
            is_holiday = jpholiday.is_holiday(date)
            if is_holiday:
                weekday_str = "祝日"

            if weekday_str not in settings:
                continue  # 対象外の日付はスキップ

            setting = settings[weekday_str]
            court_name = setting["court"].strip()
            timeslots = setting["timeslots"]

            # コートの行を特定
            try:
                court_row = dg_table_date.find_element(
                    By.XPATH, f".//tr[td[normalize-space()='{court_name}']]"
                )
            except NoSuchElementException:
                print(f"{facility_name_text} の {date_str} に '{court_name}' の行が見つかりませんでした。")
                continue

            for timeslot in timeslots:
                # 時間帯の列を特定
                try:
                    timeslot_header = dg_table_date.find_element(
                        By.XPATH, f".//tr[1]/td[contains(normalize-space(translate(., '\n', '')), '{timeslot}')]"
                    )
                    timeslot_index = timeslot_header.get_attribute("cellIndex")

                    # 対象のセルを取得
                    cell = court_row.find_element(By.XPATH, f"./td[{int(timeslot_index)+1}]")

                    # 空き状況を確認し、クリック可能ならクリック
                    try:
                        link = cell.find_element(By.TAG_NAME, "a")
                        link.click()
                        time.sleep(0.5)  # 必要に応じて調整
                        print(f"{facility_name_text} の {date_str} {court_name} {timeslot} を選択しました。")
                    except NoSuchElementException:
                        status = cell.text.strip()
                        print(f"{facility_name_text} の {date_str} {court_name} {timeslot} は予約できません。状態：{status}")
                except NoSuchElementException:
                    print(f"{facility_name_text} の {date_str} に時間帯 '{timeslot}' が見つかりませんでした。")
                    continue

    print("コートと時間帯の選択完了")

    # 次（確認画面）に進む
    driver.find_element(By.ID, "ucPCFooter_btnForward").click()
    
    # 6人にする
    driver.find_element(By.ID, "txtNinzu").send_keys("6")
    # 他も全てこれにするボタンを押下
    driver.find_element(By.ID, "orbCopyYes").click()
    # 次（申し込み画面）に進む
    driver.find_element(By.ID, "ucPCFooter_btnForward").click()
    #申し込みボタンで完了    
    driver.find_element(By.ID, "ucPCFooter_btnForward").click()
    
except Exception as e:
    print(f"エラーが発生しました: {e}")


finally:
    # ブラウザを閉じずに処理を続行する
    print("ブラウザは開いたままです。")
    while True:
        pass
