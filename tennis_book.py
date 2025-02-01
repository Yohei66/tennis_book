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
    TimeoutException
)
import calendar
import time
import re
import jpholiday
import os
import base64

# -----------------------------
# (1) Excel読み込み・特別日/通常設定の構築
# -----------------------------
excel_file = 'tennis_book_table.xlsx'  # Excelファイル名を指定

# ID列を文字列で読む
credentials_df = pd.read_excel(excel_file, sheet_name='UserCredentials', dtype={'ID': str})

# 通常の予約TimePatternシート
timepattern_df = pd.read_excel(excel_file, sheet_name='TimePattern')

# 特別日のリストシート
special_date_df = pd.read_excel(excel_file, sheet_name='SpecialDate')

# 「2025年5月18日」などを datetime に変換する関数
date_pattern_jp = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')
def parse_jp_date(date_str):
    """
    '2025年5月18日' のような文字列を datetime に変換する
    """
    match = date_pattern_jp.match(str(date_str))
    if match:
        y, m, d = map(int, match.groups())
        return datetime(y, m, d)
    return None

special_date_df['ParsedDate'] = special_date_df['SpecialDate'].apply(parse_jp_date)
special_dates = set(special_date_df['ParsedDate'].dropna().tolist())

# 特別予約パターンシート
special_book_df = pd.read_excel(excel_file, sheet_name='SpecialBook')

# 特別用 facility_settings の構築
# → {TimePattern: {FacilityName: {"特別日": {Court: [Timeslot, ...]}}}}
special_facility_settings = {}
for idx, row in special_book_df.iterrows():
    tp = str(row['TimePattern']).strip()
    facility = row['FacilityName']
    court = row['Court']
    timeslot = str(row['Timeslot']).strip()

    if tp not in special_facility_settings:
        special_facility_settings[tp] = {}
    if facility not in special_facility_settings[tp]:
        special_facility_settings[tp][facility] = {}
    # 特別日は曜日単位でなく日付単位なので、ダミーキー「特別日」とする
    if "特別日" not in special_facility_settings[tp][facility]:
        special_facility_settings[tp][facility]["特別日"] = {}
    if court not in special_facility_settings[tp][facility]["特別日"]:
        special_facility_settings[tp][facility]["特別日"][court] = []

    special_facility_settings[tp][facility]["特別日"][court].append(timeslot)

# 曜日マッピング
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
# 3か月後の日付
three_months_later = today + relativedelta(months=3)
year = three_months_later.year
month = three_months_later.month

# (オプション) Seleniumの動作設定（ヘッドレスで動かす場合など）
options = Options()
# options.add_argument("--headless")  # ヘッドレスにしたい場合

# -----------------------------
# (3) 各ユーザーごとにループ
# -----------------------------
for index, user in credentials_df.iterrows():
    user_id = str(user['ID'])
    password = str(user['Password'])
    time_pattern = str(user['TimePattern']).strip()

    print(f"=== ユーザー {user_id} の予約を開始 ===")
    print(f"TimePattern: {time_pattern}")

    # 通常TimePatternの施設設定
    user_booking_df = timepattern_df[timepattern_df['TimePattern'] == time_pattern]

    # 構築：通常 facility_settings
    # {FacilityName: { Weekday: { Court: [Timeslot,...] } } }
    normal_facility_settings = {}
    for _, row in user_booking_df.iterrows():
        fac_name = row['FacilityName']
        wd = row['Weekday']  # '月曜日' '祝日' など
        court = row['Court']
        timeslot = str(row['Timeslot']).strip()

        if fac_name not in normal_facility_settings:
            normal_facility_settings[fac_name] = {}
        if wd not in normal_facility_settings[fac_name]:
            normal_facility_settings[fac_name][wd] = {}
        if court not in normal_facility_settings[fac_name][wd]:
            normal_facility_settings[fac_name][wd][court] = []
        normal_facility_settings[fac_name][wd][court].append(timeslot)

    # 特別facility_settings (既にspecial_facility_settingsにまとめ済)
    user_special_facility = special_facility_settings.get(time_pattern, {})

    if not normal_facility_settings and not user_special_facility:
        print(f"→ 予約設定が空です。スキップします。")
        continue

    # -----------------------------
    # ブラウザ起動・ログイン
    # -----------------------------
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)
    try:
        # ログインページへ
        driver.get("https://www.pf489.com/kasukabe/web/Wg_ModeSelect.aspx")
        driver.maximize_window()

        driver.find_element(By.ID, "rbtnLogin").click()
        driver.find_element(By.ID, "txtID").send_keys(user_id)
        driver.find_element(By.ID, "txtPass").send_keys(password)
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()

        # アラートがあれば消す
        try:
            wait.until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
        except TimeoutException:
            pass

        # 通常利用方法
        driver.find_element(By.ID, "btnNormal").click()
        driver.find_element(By.ID, "rbtnYoyaku").click()
        driver.find_element(By.ID, "btnMokuteki").click()
        # 利用目的など（状況に応じて変更してください）
        driver.find_element(By.ID, "ucOecRadioButtonList_dgButtonList_ctl02_rdSelectLeft").click()
        driver.find_element(By.ID, "ucButtonList_dgButtonList_ctl03_chkSelectRight").click()
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()

        # 施設選択：通常・特別両方で出てくる施設を全てチェック
        all_facilities = set(normal_facility_settings.keys()).union(set(user_special_facility.keys()))
        for fac_name in all_facilities:
            try:
                driver.find_element(By.XPATH, f"//input[@value='{fac_name}']").click()
            except NoSuchElementException:
                print(f"施設チェックボックスが見つからず: {fac_name}")
                continue

        driver.find_element(By.ID, "ucPCFooter_btnForward").click()

        # 日付を 3か月後の year / month / 1日 に設定
        
        driver.find_element(By.ID, "txtYear").send_keys(Keys.CONTROL + "a")
        driver.find_element(By.ID, "txtYear").send_keys(Keys.DELETE)
        driver.find_element(By.ID, "txtYear").send_keys(year)
        driver.find_element(By.ID, "txtMonth").send_keys(Keys.CONTROL + "a")
        driver.find_element(By.ID, "txtMonth").send_keys(Keys.DELETE)
        driver.find_element(By.ID, "txtMonth").send_keys(month)
        driver.find_element(By.ID, "txtDay").send_keys(Keys.CONTROL + "a")
        driver.find_element(By.ID, "txtDay").send_keys(Keys.DELETE)
        driver.find_element(By.ID, "txtDay").send_keys("1")

        # 曜日チェックを全てON
        all_weekdays = ["月", "火", "水", "木", "金", "土", "日", "祝"]
        for wd_label in all_weekdays:
            checkbox = driver.find_element(By.XPATH, f"//table[@id='Table6']//input[@value='{wd_label}']")
            if not checkbox.is_selected():
                checkbox.click()

        # 次（空き照会）
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()
        wait = WebDriverWait(driver, 20)

        # --------------------------------------------------------------------
        # (A) 現在のページに「2025年5月22日（木）」などの日付テーブルが複数出てくる
        #     ここでは一度まとめてテーブルを取得してから、日付を正規表現で抜く
        # --------------------------------------------------------------------
        date_pattern_head = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')
        date_tables = driver.find_elements(By.XPATH, "//table[contains(@id, '_dgTable')]")

        for date_table in date_tables:
            # TitleColor 行の最初のセルに「2025年5月25日（○）」みたいな文字列がある
            try:
                title_cell = date_table.find_element(By.XPATH, ".//tr[@class='TitleColor']/td[1]")
                date_text = title_cell.text.strip()  # "2025年5月25日\n（火）" 等
            except NoSuchElementException:
                continue

            # 正規表現で年/月/日を抜き出す
            match_date = date_pattern_head.search(date_text)
            if not match_date:
                print(f"このテーブルの日付を取得できません: {date_text}")
                continue
            y = int(match_date.group(1))
            m = int(match_date.group(2))
            d = int(match_date.group(3))
            date_obj = datetime(y, m, d)

            # 「特別日」かどうか
            if date_obj in special_dates and time_pattern in special_facility_settings:
                # 特別日設定を使う
                fac_setting = special_facility_settings[time_pattern]
                day_key = "特別日"  # 特別日は“曜日キー”を使わない前提
                print(f"→ {date_obj.strftime('%Y/%m/%d')} は特別日(パターン:{time_pattern})")
            else:
                # 通常予約
                fac_setting = normal_facility_settings
                wd = date_obj.weekday()  # 0=月曜日, ...
                day_key = weekday_map[wd]
                if jpholiday.is_holiday(date_obj):
                    day_key = "祝日"

            # -----------------------------
            # (B) コート・時間帯 予約する
            # -----------------------------
            # このテーブルの行を取得 (最初の TitleColor 行以外)
            row_list = date_table.find_elements(By.XPATH, ".//tr[not(@class='TitleColor')]")
            # 施設名は既に上階層でクリック済なので「施設名に合わせる」作業は不要
            # 各行先頭セルに「共用C」「硬式B」などの文字が入っている
            # day_key が無ければスキップ
            # ただし“fac_setting” のキーは「施設名→曜日(or特別日)→コート...」の階層構造
            # 施設名は TitleColor 部分に表示されてるが、ここでは date_table の "上位" には
            # "大沼公園グラウンド" などが書かれているので、取得してキーに使う
            # → 施設名取得
            try:
                facility_label = date_table.find_element(
                    By.XPATH,
                    ".//ancestor::table[contains(@id,'tpItem')][1]//span[contains(@id,'lblShisetsu')]"
                )
                facility_name_text = facility_label.text.strip()
            except NoSuchElementException:
                # 施設名リンク(aタグ)パターンの場合
                try:
                    facility_link = date_table.find_element(
                        By.XPATH,
                        ".//ancestor::table[contains(@id,'tpItem')][1]//a[contains(@id,'lnkShisetsu')]"
                    )
                    facility_name_text = facility_link.text.strip()
                except NoSuchElementException:
                    # 施設名が取得できない
                    facility_name_text = ""

            if facility_name_text not in fac_setting:
                # 対象外施設
                continue
            if day_key not in fac_setting[facility_name_text]:
                # この曜日/特別日には予約設定が無い
                continue

            # 予約対象： { CourtName: [Timeslot, ...] }
            court_dict = fac_setting[facility_name_text][day_key]

            # 各行(コート行)を順番にスキャン
            for row in row_list:
                try:
                    # 先頭セルがコート名
                    court_name = row.find_element(By.XPATH, ".//td[1]").text.strip()
                except NoSuchElementException:
                    continue

                if court_name not in court_dict:
                    # 予約対象外のコートならスキップ
                    continue

                # 該当コートのタイムスロットリストを取得
                timeslots = court_dict[court_name]
                if not timeslots:
                    continue

                # テーブルのヘッダ行（TitleColor 行）の時間帯順序に合わせてセルを特定
                # 2列目: 定員 → 3列目以降が時間帯
                # 先頭行(TitleColor)の <td> のうち、"9:00～\n11:00" のような文字に timeslot が含まれるかどうかで判定
                # ここでは簡略化して: 
                header_cells = date_table.find_elements(By.XPATH, ".//tr[@class='TitleColor']/td")
                # 時間列は header_cells[2] 以降

                for timeslot in timeslots:
                    # 例) timeslot = "9:00～11:00"
                    found_col_index = None
                    for col_idx in range(2, len(header_cells)):
                        header_text = header_cells[col_idx].text.replace('\n', '').replace(' ', '')
                        # "9:00～11:00" のような文字列になっている
                        if timeslot == header_text:
                            found_col_index = col_idx
                            break

                    if found_col_index is None:
                        print(f"{facility_name_text} {court_name} タイムスロット見つからず: {timeslot}")
                        continue

                    # 該当セルをクリック (row の found_col_index 番目の <td>)
                    try:
                        cell = row.find_element(By.XPATH, f".//td[{found_col_index+1}]")
                        # aタグあれば予約可
                        link = cell.find_element(By.TAG_NAME, "a")
                        link.click()
                        time.sleep(0.2)
                        print(f"予約選択: {date_obj.strftime('%Y/%m/%d')} {facility_name_text} {court_name} {timeslot}")
                    except NoSuchElementException:
                        status = cell.text.strip() if cell else "不明"
                        print(f"{date_obj.strftime('%Y/%m/%d')} {facility_name_text} {court_name} {timeslot} は予約不可: {status}")
                    except Exception as e:
                        print(f"{date_obj.strftime('%Y/%m/%d')} {facility_name_text} {court_name} {timeslot} でエラー: {e}")
                        continue

        # -----------------------------
        # (C) 次へ（確認画面）に進む
        # -----------------------------
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()

        # 利用人数を6人に
        try:
            driver.find_element(By.ID, "txtNinzu").send_keys("6")
            driver.find_element(By.ID, "orbCopyYes").click()
        except NoSuchElementException:
            # 人数指定が不要な場合はスキップ
            pass

        # 申し込み画面へ
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()

        # 申し込み確定→PDF保存
        try:
            driver.find_element(By.ID, "ucPCFooter_btnForward").click()
            # アラートが出る場合（既に予約済など）
            try:
                WebDriverWait(driver, 5).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                print(f"→ アラート発生: {alert_text} (予約重複などの可能性)")
            except TimeoutException:
                pass

            # PDF出力(任意)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.join(script_dir, "PDF")
            os.makedirs(base_dir, exist_ok=True)
            now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_file_name = f"{user_id}_{now_str}.pdf"
            pdf_file_path = os.path.join(base_dir, pdf_file_name)

            settings = {
                'landscape': False,
                'displayHeaderFooter': False,
                'printBackground': True,
                'preferCSSPageSize': True
            }
            pdf_data = driver.execute_cdp_cmd("Page.printToPDF", settings)
            with open(pdf_file_path, 'wb') as f:
                f.write(base64.b64decode(pdf_data['data']))

            print(f"PDF保存: {pdf_file_path}")

        except Exception as e:
            print(f"完了処理中にエラー: {e}")

        print(f"→ ユーザー {user_id} の予約完了")

    except Exception as e:
        print(f"例外が発生しました: {e}")
    finally:
        driver.quit()

print("全ユーザーの予約処理が完了しました。")
