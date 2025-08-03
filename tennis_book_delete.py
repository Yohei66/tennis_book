import pandas as pd
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
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException
)
import calendar
import time
import re
import jpholiday
import os
import base64
import logging

# -----------------------------
# ログの設定（ログファイル: reservation_log.log）
# -----------------------------
logging.basicConfig(
    filename='reservation_log.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

logger.info("実行開始")

# -----------------------------
# 共通関数: 安全にクリックするための再試行処理
# -----------------------------
def safe_click(wait, by, locator, attempts=3, delay=1):
    for attempt in range(attempts):
        try:
            element = wait.until(EC.element_to_be_clickable((by, locator)))
            element.click()
            return
        except StaleElementReferenceException:
            if attempt < attempts - 1:
                time.sleep(delay)
            else:
                raise

# -----------------------------
# (1) Excel読み込み・特別日/通常設定の構築
# -----------------------------
excel_file = 'tennis_book_table_dev.xlsx'  # Excelファイル名

credentials_df = pd.read_excel(excel_file, sheet_name='UserCredentials', dtype={'ID': str})
timepattern_df = pd.read_excel(excel_file, sheet_name='TimePattern')
special_date_df = pd.read_excel(excel_file, sheet_name='SpecialDate')
special_book_df = pd.read_excel(excel_file, sheet_name='SpecialBook')

date_pattern_jp = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')
def parse_jp_date(date_str):
    match = date_pattern_jp.match(str(date_str))
    if match:
        y, m, d = map(int, match.groups())
        return datetime(y, m, d)
    return None

special_date_df['ParsedDate'] = special_date_df['SpecialDate'].apply(parse_jp_date)
special_dates = set(d.date() for d in special_date_df['SpecialDate'].dropna())

logger.info("SpecialDate シート内容:\n%s", special_date_df)
logger.info("parse_jp_date の結果:")
for idx, row in special_date_df.iterrows():
    raw_str = row['SpecialDate']
    parsed = parse_jp_date(raw_str)
    logger.info("  行%d: 原文=%s → 変換=%s", idx, repr(raw_str), parsed)
logger.info("special_dates に格納された日付: %s", list(special_dates))

# 特別用 facility_settings: {TimePattern: {FacilityName: {"特別日": {Court:[Timeslot,...]}}}}
special_facility_settings = {}
for idx, row in special_book_df.iterrows():
    tp = str(row['TimePattern']).strip()
    facility = str(row['FacilityName']).strip()
    court = str(row['Court']).strip()
    timeslot = str(row['Timeslot']).strip()

    if tp not in special_facility_settings:
        special_facility_settings[tp] = {}
    if facility not in special_facility_settings[tp]:
        special_facility_settings[tp][facility] = {}
    if "特別日" not in special_facility_settings[tp][facility]:
        special_facility_settings[tp][facility]["特別日"] = {}
    if court not in special_facility_settings[tp][facility]["特別日"]:
        special_facility_settings[tp][facility]["特別日"][court] = []
    special_facility_settings[tp][facility]["特別日"][court].append(timeslot)

# 通常の曜日名マッピング
weekday_map = {
    0: "月曜日",
    1: "火曜日",
    2: "水曜日",
    3: "木曜日",
    4: "金曜日",
    5: "土曜日",
    6: "日曜日",
}

# -----------------------------
# (2) 予約実行の準備
# -----------------------------
today = datetime.today()
three_months_later = today + relativedelta(months=3)
year = three_months_later.year
month = three_months_later.month
day = 1  # 月初

options = Options()
# options.add_argument("--headless")

# -----------------------------
# (3) 各ユーザーごとに予約
# -----------------------------
for i, user in credentials_df.iterrows():
    user_id = user['ID']
    user_name = user['Name']
    password = user['Password']
    time_pattern = str(user['TimePattern']).strip()

    logger.info("=== ユーザー %s の予約を開始 ===", user_id)
    logger.info("TimePattern: %s", time_pattern)

    # 通常facility_settingsの構築
    user_booking_df = timepattern_df[timepattern_df['TimePattern'] == time_pattern]
    normal_facility_settings = {}
    for _, row in user_booking_df.iterrows():
        fac = str(row['FacilityName']).strip()
        wd = str(row['Weekday']).strip()
        court = str(row['Court']).strip()
        timeslot = str(row['Timeslot']).strip()

        if fac not in normal_facility_settings:
            normal_facility_settings[fac] = {}
        if wd not in normal_facility_settings[fac]:
            normal_facility_settings[fac][wd] = {}
        if court not in normal_facility_settings[fac][wd]:
            normal_facility_settings[fac][wd][court] = []
        normal_facility_settings[fac][wd][court].append(timeslot)

    # 特別facility_settings
    user_special_facility = special_facility_settings.get(time_pattern, {})

    # WebDriver起動
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    wait = WebDriverWait(driver, 20)
    try:
        # --- ログイン ---
        driver.get("https://www.pf489.com/kasukabe/web/Wg_ModeSelect.aspx")
        driver.maximize_window()
        safe_click(wait, By.ID, "rbtnLogin")
        wait.until(EC.visibility_of_element_located((By.ID, "txtID")))
        driver.find_element(By.ID, "txtID").send_keys(user_id)
        wait.until(EC.visibility_of_element_located((By.ID, "txtPass")))
        driver.find_element(By.ID, "txtPass").send_keys(password)
        safe_click(wait, By.ID, "ucPCFooter_btnForward")

        # アラート処理
        try:
            wait.until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
            logger.info("ログイン後のアラートを受け付けました")
        except TimeoutException:
            pass

        logger.info("ログイン後 - 利用方法選択へ遷移")

        # --- 通常利用方法など一連の操作 ---
        safe_click(wait, By.ID, "btnNormal")
        safe_click(wait, By.ID, "rbtnChusen")
        logger.info("取り消しボタンのクリック開始")
        # IDがパターンに一致するすべての要素をクリック  
        torikeshi_buttons = driver.find_elements(
            By.XPATH,
            "//input[starts-with(@id, 'dlRepeat_ctl')and contains(@id, '_tpItem_dgTable_ctl') and contains(@id, '_chkTorikeshi') and @type='submit']"
        )
        for btn in torikeshi_buttons:
            try:
                # disabled属性がある場合はスキップ
                if btn.get_attribute("disabled"):
                    logger.info(f"スキップ（disabled）: {btn.get_attribute('id')}")
                    continue
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                wait.until(EC.element_to_be_clickable(btn))
                driver.execute_script("arguments[0].click();", btn)
                logger.info(f"クリック: {btn.get_attribute('id')}")
            except Exception as e:
                logger.warning(f"クリック失敗: {btn.get_attribute('id')} - {repr(e)}")
        # クリック後、1分間ウィンドウを開いたままにする
        # logger.info("クリック後、1分間ウィンドウを保持します。")
        
        safe_click(wait, By.ID, "ucPCFooter_btnForward")
        safe_click(wait, By.ID, "ucPCFooter_btnForward")
        time.sleep(10)
    finally:
        driver.quit()

logger.info("全ユーザーの予約処理が完了しました。")
