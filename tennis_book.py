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
excel_file = 'tennis_book_table.xlsx'  # Excelファイル名

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
        safe_click(wait, By.ID, "rbtnYoyaku")
        safe_click(wait, By.ID, "btnMokuteki")
        safe_click(wait, By.ID, "ucOecRadioButtonList_dgButtonList_ctl02_rdSelectLeft")
        safe_click(wait, By.ID, "ucButtonList_dgButtonList_ctl03_chkSelectRight")
        safe_click(wait, By.ID, "ucPCFooter_btnForward")
        safe_click(wait, By.ID, "ucPCFooter_btnForward")

        logger.info("利用目的・種別を選択完了")

        # 施設選択
        all_facilities = set(normal_facility_settings.keys()).union(set(user_special_facility.keys()))
        logger.info("▼ 選択対象の施設一覧: %s", list(all_facilities))
        for fac_name in all_facilities:
            try:
                logger.info("施設チェック: %s のチェックボックスを探します", fac_name)
                elem_fac = wait.until(EC.presence_of_element_located((By.XPATH, f"//input[@value='{fac_name}']")))
                elem_fac.click()
                logger.info(" → %s チェック成功", fac_name)
            except NoSuchElementException:
                logger.error(" → 施設チェックボックス見つからず: %s (スキップ)", fac_name)

        safe_click(wait, By.ID, "ucPCFooter_btnForward")
        logger.info("施設選択完了")

        # 日付設定画面へ遷移した後、txtYear, txtMonth, txtDay の表示を待つ
        wait.until(EC.visibility_of_element_located((By.ID, "txtYear")))
        wait.until(EC.visibility_of_element_located((By.ID, "txtMonth")))
        wait.until(EC.visibility_of_element_located((By.ID, "txtDay")))

        # 日付設定 (3か月後の初日)
        txtYear = driver.find_element(By.ID, "txtYear")
        txtYear.clear()
        txtYear.send_keys(str(year))

        txtMonth = driver.find_element(By.ID, "txtMonth")
        txtMonth.clear()
        txtMonth.send_keys(str(month))

        txtDay = driver.find_element(By.ID, "txtDay")
        txtDay.clear()
        txtDay.send_keys("1")
        safe_click(wait, By.ID, "rbtnMonth")

        # 曜日のチェックボックスをすべてON
        all_weekdays = ["月", "火", "水", "木", "金", "土", "日", "祝"]
        for w in all_weekdays:
            try:
                chk = driver.find_element(By.XPATH, f"//table[@id='Table6']//input[@value='{w}']")
                if not chk.is_selected():
                    chk.click()
            except NoSuchElementException:
                logger.error("曜日チェックボックスが見つからない: %s", w)

        driver.find_element(By.ID, "ucPCFooter_btnForward").click()
        time.sleep(2)
        logger.info("(A) 施設別空き状況ページ到達")

        # 「抽選」リンクを全てクリック（都度取得して再試行）
        while True:
            try:
                chusen_links = driver.find_elements(By.XPATH, "//a[text()='抽選']")
                if not chusen_links:
                    break
                for link in chusen_links:
                    link.click()
                    time.sleep(0.2)
                break
            except StaleElementReferenceException:
                continue

        safe_click(wait, By.ID, "ucPCFooter_btnForward")
        time.sleep(2)
        logger.info("(B) 時間帯別空き状況ページ到達 - ここでコート/時間帯をクリック")

        any_timeslot_clicked = False
        date_pattern_head = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')
        date_tables = driver.find_elements(By.XPATH, "//table[contains(@id, '_dgTable')]")
        logger.info("  → 日付テーブル数: %d", len(date_tables))

        for date_table in date_tables:
            try:
                title_cell = date_table.find_element(By.XPATH, ".//tr[@class='TitleColor']/td[1]")
                date_text = title_cell.text.strip()
            except NoSuchElementException:
                logger.error("    → TitleColor行が見つからないテーブル(スキップ)")
                continue

            match_date = date_pattern_head.search(date_text)
            if not match_date:
                logger.error("    → 日付テキスト解析できず: %s (スキップ)", date_text)
                continue

            y = int(match_date.group(1))
            m = int(match_date.group(2))
            d = int(match_date.group(3))
            date_obj = datetime(y, m, d)
            logger.info("\n  *** 対象日付テーブル: %s ***", date_obj.strftime('%Y/%m/%d'))

            if date_obj.date() in special_dates and time_pattern in special_facility_settings:
                fac_setting = special_facility_settings[time_pattern]
                day_key = "特別日"
                logger.info("    → %s は特別日", date_obj.strftime('%Y/%m/%d'))
            else:
                fac_setting = normal_facility_settings
                wd = date_obj.weekday()
                day_key = weekday_map[wd]
                if jpholiday.is_holiday(date_obj):
                    day_key = "祝日"
                logger.info("    → %s は day_key=%s", date_obj.strftime('%Y/%m/%d'), day_key)

            try:
                facility_label = date_table.find_element(
                    By.XPATH, "./preceding::*[contains(@id, '_lblShisetsu') or contains(@id, '_lnkShisetsu')][1]"
                )
                facility_name_text = facility_label.text.strip()
            except NoSuchElementException:
                try:
                    facility_link = date_table.find_element(
                        By.XPATH, ".//ancestor::table[contains(@id,'tpItem')][1]//a[contains(@id,'lnkShisetsu')]"
                    )
                    facility_name_text = facility_link.text.strip()
                except NoSuchElementException:
                    facility_name_text = ""

            if facility_name_text not in fac_setting:
                logger.error("    → 施設:%s は設定に存在しない (スキップ)", facility_name_text)
                continue

            if day_key not in fac_setting[facility_name_text]:
                logger.error("    → day_key:%s は %s の設定に存在しない (スキップ)", day_key, facility_name_text)
                continue

            court_dict = fac_setting[facility_name_text][day_key]
            row_list = date_table.find_elements(By.XPATH, ".//tr[not(@class='TitleColor')]")
            logger.info("    → コート行の件数: %d", len(row_list))
            header_cells = date_table.find_elements(By.XPATH, ".//tr[@class='TitleColor']/td")
            logger.info("    → ヘッダセルの件数: %d", len(header_cells))

            for row_elem in row_list:
                try:
                    court_name = row_elem.find_element(By.XPATH, ".//td[1]").text.strip()
                except NoSuchElementException:
                    continue

                if court_name not in court_dict:
                    continue

                timeslots = court_dict[court_name]
                if not timeslots:
                    logger.error("      → コート:%s は設定にTimeslotが無い (スキップ)", court_name)
                    continue

                for tslot in timeslots:
                    found_col_index = None
                    for c_idx in range(2, len(header_cells)):
                        head_text_raw = header_cells[c_idx].text
                        head_text = head_text_raw.replace('\n','').replace(' ','')
                        if tslot == head_text:
                            found_col_index = c_idx
                            break
                    if found_col_index is None:
                        logger.error("      → (不一致) %s/%s/%s がヘッダと合わずクリック不可", facility_name_text, court_name, tslot)
                        continue

                    try:
                        cell = row_elem.find_element(By.XPATH, f"./td[{found_col_index+1}]")
                    except NoSuchElementException:
                        logger.error("      → 該当セルが存在しない (colIndex=%s)", found_col_index)
                        continue

                    try:
                        link = cell.find_element(By.TAG_NAME, "a")
                        link.click()
                        logger.info("      → 予約選択: %s %s %s %s", date_obj.strftime('%Y/%m/%d'), facility_name_text, court_name, tslot)
                        any_timeslot_clicked = True
                        time.sleep(0.2)
                    except NoSuchElementException:
                        status = cell.text.strip() if cell else "不明"
                        logger.error("      → 予約不可: %s %s %s → %s", facility_name_text, court_name, tslot, status)

        if not any_timeslot_clicked:
            logger.error("◆◆◆ このページで1枠も時間帯をクリックしなかったため、次画面でエラーになる可能性があります ◆◆◆")
            # 必要に応じて処理を中断する等対応

        # -----------------------------
        # (C) 確認画面 → 申し込み → PDF保存
        # -----------------------------
        safe_click(wait, By.ID, "ucPCFooter_btnForward")
        logger.info("(C) 確認画面へ遷移")

        wait.until(EC.visibility_of_element_located((By.ID, "txtNinzu")))
        driver.find_element(By.ID, "txtNinzu").send_keys("6")
        safe_click(wait, By.ID, "orbCopyYes")
        safe_click(wait, By.ID, "ucPCFooter_btnForward")
        logger.info("人数・コピー選択完了")

        time.sleep(1)
        attempt = 0
        max_attempts = 3
        while attempt < max_attempts:
            try:
                safe_click(wait, By.ID, "ucPCFooter_btnForward")
                break
            except StaleElementReferenceException:
                logger.warning("StaleElementReferenceException 発生：再試行します (最終確認)")
                attempt += 1
                time.sleep(1)

        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            text_ = alert.text
            alert.accept()
            logger.info("アラート発生: %s", text_)
        except TimeoutException:
            pass

        time.sleep(1)
        attempt = 0
        max_attempts = 3
        while attempt < max_attempts:
            try:
                settings = {
                    'landscape': False,
                    'displayHeaderFooter': False,
                    'printBackground': True,
                    'preferCSSPageSize': True
                }
                pdf_data = driver.execute_cdp_cmd("Page.printToPDF", settings)
                break
            except StaleElementReferenceException:
                logger.warning("StaleElementReferenceException 発生：PDF保存再試行")
                attempt += 1
                time.sleep(1)

        # PDF保存処理
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.join(script_dir, "PDF")
        current_month_folder = datetime.now().strftime('%Y%m')
        output_dir = os.path.join(base_dir, current_month_folder)
        os.makedirs(output_dir, exist_ok=True)
        now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_name = f"{user_id}_{user_name}_{now_str}.pdf"
        pdf_path = os.path.join(output_dir, pdf_name)
        with open(pdf_path, 'wb') as f:
            f.write(base64.b64decode(pdf_data['data']))

        logger.info("PDF保存: %s", pdf_path)
        logger.info("→ ユーザー %s の予約完了", user_id)

    except Exception as e:
        logger.error("ユーザー %s の予約処理中に例外発生: %s", user_id, e)
    finally:
        driver.quit()

logger.info("全ユーザーの予約処理が完了しました。")
