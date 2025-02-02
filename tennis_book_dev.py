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
    NoAlertPresentException,
    NoSuchElementException,
    UnexpectedAlertPresentException,
    TimeoutException
)
import calendar
import time
import re
import jpholiday
import os
import base64

# Excelファイルの読み込み
excel_file = 'tennis_book_table.xlsx'  # Excelファイル名を指定してください

# ID列を文字列型として読み込む
credentials_df = pd.read_excel(excel_file, sheet_name='UserCredentials', dtype={'ID': str})
timepattern_df = pd.read_excel(excel_file, sheet_name='TimePattern')

# 今日の日付を取得
today = datetime.today()

# 3か月後の日付を計算
three_months_later = today + relativedelta(months=3)

# 年、月、日に分解
year = three_months_later.year
month = three_months_later.month
day = three_months_later.day

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

# ユーザーごとに処理
for index, user in credentials_df.iterrows():
    id = str(user['ID'])
    password = str(user['Password'])
    time_pattern = user['TimePattern']
    
    # ユーザーの予約設定を取得
    user_booking_df = timepattern_df[timepattern_df['TimePattern'] == time_pattern]
    
    # デバッグ用の出力
    print(f"\n=== {id} の予約処理を開始します ===")
    print(f"TimePattern: {time_pattern}")
    print("User booking settings:")
    print(user_booking_df)
    
    # facility_settingsを構築
    facility_settings = {}
    for _, row in user_booking_df.iterrows():
        facility_name = row['FacilityName']
        weekday = row['Weekday']
        court = row['Court']
        timeslot = str(row['Timeslot']).strip()
        
        if facility_name not in facility_settings:
            facility_settings[facility_name] = {}
        if weekday not in facility_settings[facility_name]:
            facility_settings[facility_name][weekday] = {}
        if court not in facility_settings[facility_name][weekday]:
            facility_settings[facility_name][weekday][court] = []
        
        facility_settings[facility_name][weekday][court].append(timeslot)
    
    # デバッグ：facility_settingsを表示
    print(f"\nConstructed facility_settings for ID {id}:")
    print(facility_settings)
    
    # facility_settingsが空の場合、次のユーザーに進む
    if not facility_settings:
        print(f"{id} の予約設定がありません。次のユーザーに進みます。")
        continue
    
    # WebDriverを初期化
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
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
        wait.until(EC.alert_is_present())
        alert = driver.switch_to.alert
        alert.accept()
    except TimeoutException:
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
        try:
            element = driver.find_element(By.XPATH, f"//input[@value='{facility_name}']")
            element.click()
        except NoSuchElementException:
            print(f"{facility_name} のチェックボックスが見つかりませんでした。")
            continue

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
        for facility_name, weekdays in facility_settings.items():
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

                    if weekday_str in weekdays:
                        dates_to_click.append((date, weekdays[weekday_str]))

                # 対象の日付の要素をクリック
                for date, courts in dates_to_click:
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

            weekdays = facility_settings[facility_name_text]

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

                if weekday_str not in weekdays:
                    continue  # 対象外の日付はスキップ

                courts = weekdays[weekday_str]

                for court_name, timeslots in courts.items():
                    court_name = court_name.strip()
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
       
        # 完了ボタン押下後のアラート処理とスクリーンショット保存
        try:
            # 完了ボタンをクリック
            driver.find_element(By.ID, "ucPCFooter_btnForward").click()
            
            # アラートが表示された場合、予約済みとして処理を終了
            try:
                WebDriverWait(driver, 5).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                print("予約済みです。処理を中止します。")
                alert.accept()
                continue  # 次のユーザーの処理へ
            except TimeoutException:
                # アラートが表示されなかった場合、次の画面に遷移したと判断
                pass
            
            # 現在のスクリプトのディレクトリを基準に、PDFフォルダのパスを取得
            script_dir = os.path.dirname(os.path.abspath(__file__))  # Pythonファイルのディレクトリ
            base_dir = os.path.join(script_dir, "PDF")  # PDFフォルダへの相対パス

            # 今月のフォルダ名を生成
            current_month_folder = datetime.now().strftime('%Y%m')  # 「YYYYMM」形式でフォルダ名を生成
            output_dir = os.path.join(base_dir, current_month_folder)  # 今月のフォルダのパス

            # フォルダが存在しない場合、作成
            os.makedirs(output_dir, exist_ok=True)

            # PDFファイル名をIDと日時で設定
            current_time = datetime.now().strftime('%Y%m%d_%H%M%S')  # 日時を「YYYYMMDD_HHMMSS」の形式で取得
            pdf_file_name = f"{id}_{current_time}.pdf"  # ファイル名を「ID_YYYYMMDD_HHMMSS.pdf」に設定
            pdf_file_path = os.path.join(output_dir, pdf_file_name)

            # PDFの保存設定
            settings = {
                'landscape': False,                # 縦向き
                'displayHeaderFooter': False,
                'printBackground': True,           # 背景を含める
                'preferCSSPageSize': True
            }

            # Chromeのデベロッパー機能を使ってページをPDFとして保存
            pdf_data = driver.execute_cdp_cmd("Page.printToPDF", settings)

            # PDFファイルとして保存
            with open(pdf_file_path, 'wb') as f:
                f.write(base64.b64decode(pdf_data['data']))

            print(f"ページ全体をPDFとして保存しました: {pdf_file_path}")
            
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")

        print(f"{id} の予約処理が完了しました。")
                    

    except Exception as e:
        print(f"エラーが発生しました: {e}")
    
    finally:
        # ブラウザを閉じる
        driver.quit()

print("全ての予約処理が完了しました。")
