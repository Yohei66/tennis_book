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
excel_file = 'tennis_book_table.xlsx'  # Excelファイル名

credentials_df = pd.read_excel(excel_file, sheet_name='UserCredentials', dtype={'ID': str})
timepattern_df = pd.read_excel(excel_file, sheet_name='TimePattern')
special_date_df = pd.read_excel(excel_file, sheet_name='SpecialDate')
special_book_df = pd.read_excel(excel_file, sheet_name='SpecialBook')

# 日付文字列(例 '2025年5月18日') を datetime に変換する関数
date_pattern_jp = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')
def parse_jp_date(date_str):
    match = date_pattern_jp.match(str(date_str))
    if match:
        y, m, d = map(int, match.groups())
        return datetime(y, m, d)
    return None

special_date_df['ParsedDate'] = special_date_df['SpecialDate'].apply(parse_jp_date)
special_dates = set(special_date_df['ParsedDate'].dropna().tolist())

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
    password = user['Password']
    time_pattern = str(user['TimePattern']).strip()

    print(f"\n=== ユーザー {user_id} の予約を開始 ===")
    print(f"TimePattern: {time_pattern}")

    # 通常facility_settings
    user_booking_df = timepattern_df[timepattern_df['TimePattern'] == time_pattern]
    normal_facility_settings = {}
    for _, row in user_booking_df.iterrows():
        fac = str(row['FacilityName']).strip()
        wd = str(row['Weekday']).strip()  # "月曜日", "祝日" など
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
        driver.find_element(By.ID, "rbtnLogin").click()
        driver.find_element(By.ID, "txtID").send_keys(user_id)
        driver.find_element(By.ID, "txtPass").send_keys(password)
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()

        # アラート処理
        try:
            wait.until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
        except TimeoutException:
            pass

        print("ログイン後 - 利用方法選択へ遷移")

        # --- 通常利用方法など一連の操作 ---
        driver.find_element(By.ID, "btnNormal").click()
        driver.find_element(By.ID, "rbtnYoyaku").click()
        driver.find_element(By.ID, "btnMokuteki").click()
        driver.find_element(By.ID, "ucOecRadioButtonList_dgButtonList_ctl02_rdSelectLeft").click()
        driver.find_element(By.ID, "ucButtonList_dgButtonList_ctl03_chkSelectRight").click()
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()

        print("利用目的・種別を選択完了")

        # 施設選択
        all_facilities = set(normal_facility_settings.keys()).union(
            set(user_special_facility.keys())
        )
        print(f"▼ 選択対象の施設一覧: {list(all_facilities)}")
        for fac_name in all_facilities:
            try:
                print(f"施設チェック: {fac_name} のチェックボックスを探します")
                elem_fac = driver.find_element(By.XPATH, f"//input[@value='{fac_name}']")
                elem_fac.click()
                print(f" → {fac_name} チェック成功")
            except NoSuchElementException:
                print(f" → 施設チェックボックス見つからず: {fac_name} (スキップ)")

        driver.find_element(By.ID, "ucPCFooter_btnForward").click()
        print("施設選択完了")

        # 日付設定 (2025/05/01 のように 3か月後の year/month/1日)
        txtYear = driver.find_element(By.ID, "txtYear")
        txtYear.clear()
        txtYear.send_keys(str(year))

        txtMonth = driver.find_element(By.ID, "txtMonth")
        txtMonth.clear()
        txtMonth.send_keys(str(month))

        txtDay = driver.find_element(By.ID, "txtDay")
        txtDay.clear()
        txtDay.send_keys("1")
        
        driver.find_element(By.ID, "rbtnMonth").click()

        # 曜日のチェックボックスをすべてON
        all_weekdays = ["月", "火", "水", "木", "金", "土", "日", "祝"]
        for w in all_weekdays:
            try:
                chk = driver.find_element(By.XPATH, f"//table[@id='Table6']//input[@value='{w}']")
                if not chk.is_selected():
                    chk.click()
                #print(f"曜日チェック: {w} (ON済)")
            except NoSuchElementException:
                print(f"曜日チェックボックスが見つからない: {w}")

        # 次へ（施設別空き状況ページ）
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()
        time.sleep(2)

        print("(A) 施設別空き状況ページ到達")

        # (A)-1) "抽選"リンクを全てクリック
        all_chusen_links = driver.find_elements(By.XPATH, "//a[text()='抽選']")
        print(f"抽選リンクの件数: {len(all_chusen_links)}")

        for link in all_chusen_links:
            try:
                # デバッグ: リンクの outerHTML などを確認すると、何が取得されているか分かりやすい
                # print("抽選リンクHTML:", link.get_attribute('outerHTML'))
                link.click()
                print(" → 抽選を1件クリックしました。")
                time.sleep(0.2)
            except Exception as e:
                print(f"抽選クリック失敗: {e}")

        # (A)-2) 「次へ >>」ボタン（時間帯別空き状況ページへ）
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()
        time.sleep(2)

        print("(B) 時間帯別空き状況ページ到達 - ここでコート/時間帯をクリック")

        # ここで 1つでもクリックできたかどうかのフラグ
        any_timeslot_clicked = False

        date_pattern_head = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')
        date_tables = driver.find_elements(By.XPATH, "//table[contains(@id, '_dgTable')]")
        print(f"  → 日付テーブル数: {len(date_tables)}")

        for date_table in date_tables:
            # ヘッダーの「TitleColor」行から日付テキストを取る
            try:
                title_cell = date_table.find_element(By.XPATH, ".//tr[@class='TitleColor']/td[1]")
                date_text = title_cell.text.strip()
            except NoSuchElementException:
                print("    → TitleColor行が見つからないテーブル(スキップ)")
                continue

            match_date = date_pattern_head.search(date_text)
            if not match_date:
                print(f"    → 日付テキスト解析できず: {date_text} (スキップ)")
                continue

            y = int(match_date.group(1))
            m = int(match_date.group(2))
            d = int(match_date.group(3))
            date_obj = datetime(y, m, d)
            print(f"\n  *** 対象日付テーブル: {date_obj.strftime('%Y/%m/%d')} ***")

            # 特別日 or 通常日を判定
            if date_obj in special_dates and time_pattern in special_facility_settings:
                fac_setting = special_facility_settings[time_pattern]
                day_key = "特別日"
                print(f"    → {date_obj.strftime('%Y/%m/%d')} は特別日")
            else:
                fac_setting = normal_facility_settings
                wd = date_obj.weekday()
                day_key = weekday_map[wd]
                if jpholiday.is_holiday(date_obj):
                    day_key = "祝日"
                print(f"    → {date_obj.strftime('%Y/%m/%d')} は day_key={day_key}")

            # 施設名の取得
            try:
                facility_label = date_table.find_element(
                    By.XPATH, ".//ancestor::table[contains(@id,'tpItem')][1]//span[contains(@id,'lblShisetsu')]"
                )
                facility_name_text = facility_label.text.strip()
            except NoSuchElementException:
                # 施設がaタグになってるケース
                try:
                    facility_link = date_table.find_element(
                        By.XPATH, ".//ancestor::table[contains(@id,'tpItem')][1]//a[contains(@id,'lnkShisetsu')]"
                    )
                    facility_name_text = facility_link.text.strip()
                except NoSuchElementException:
                    facility_name_text = ""

            if facility_name_text not in fac_setting:
                print(f"    → 施設:{facility_name_text} は設定に存在せず(スキップ)")
                continue

            if day_key not in fac_setting[facility_name_text]:
                print(f"    → day_key:{day_key} は {facility_name_text} の設定に存在しない(スキップ)")
                continue

            court_dict = fac_setting[facility_name_text][day_key]

            # タイトル行以外を取得
            row_list = date_table.find_elements(By.XPATH, ".//tr[not(@class='TitleColor')]")
            print(f"    → コート行の件数: {len(row_list)}")
            # ヘッダー行(時間帯セル)
            header_cells = date_table.find_elements(By.XPATH, ".//tr[@class='TitleColor']/td")
            print(f"    → ヘッダセルの件数: {len(header_cells)}")

            for row_elem in row_list:
                try:
                    court_name = row_elem.find_element(By.XPATH, ".//td[1]").text.strip()
                except NoSuchElementException:
                    continue

                if court_name not in court_dict:
                    # デバッグ: コート名がマッチしない理由を調べる
                    # print(f"      → コート:{court_name} は設定に無いのでスキップ")
                    continue

                timeslots = court_dict[court_name]
                if not timeslots:
                    print(f"      → コート:{court_name} は設定にTimeslotが無い (スキップ)")
                    continue

                # ヘッダーの時間帯セルを順にチェック
                for tslot in timeslots:
                    found_col_index = None
                    for c_idx in range(2, len(header_cells)):
                        # 例) ヘッダセルテキスト: "9:00～11:00" (改行・空白削除)
                        head_text_raw = header_cells[c_idx].text
                        head_text = head_text_raw.replace('\n','').replace(' ','')
                        
                        # デバッグ出力
                        # print(f"        ヘッダ比較: tslot={tslot} / head_text={head_text}")
                        
                        if tslot == head_text:
                            found_col_index = c_idx
                            break

                    if found_col_index is None:
                        print(f"      → (不一致) {facility_name_text}/{court_name}/"
                              f"{tslot} がヘッダと合わずクリック不可")
                        continue

                    # クリック対象のセルを取得
                    try:
                        cell = row_elem.find_element(By.XPATH, f"./td[{found_col_index+1}]")
                    except NoSuchElementException:
                        print(f"      → 該当セルが存在しない (colIndex={found_col_index})")
                        continue

                    # aタグがあるかどうかチェック
                    try:
                        link = cell.find_element(By.TAG_NAME, "a")
                        link.click()
                        print(f"      → 予約選択: {date_obj.strftime('%Y/%m/%d')} {facility_name_text} {court_name} {tslot}")
                        any_timeslot_clicked = True
                        time.sleep(0.2)
                    except NoSuchElementException:
                        status = cell.text.strip() if cell else "不明"
                        print(f"      → 予約不可: {facility_name_text} {court_name} {tslot} → {status}")

        # もし1つも時間帯クリックが無かった場合、次ページでエラーになるので注意
        if not any_timeslot_clicked:
            print("◆◆◆ このページで1枠も時間帯をクリックしなかったため、次画面でエラーになる可能性があります ◆◆◆")
            # 必要に応じて下記のようにスキップする:
            # driver.quit()
            # continue

        # -----------------------------
        # (C) 確認画面 → 申し込み → PDF保存
        # -----------------------------
        driver.find_element(By.ID, "ucPCFooter_btnForward").click()
        print("(C) 確認画面へ遷移")

        # 人数6人
        try:
            driver.find_element(By.ID, "txtNinzu").send_keys("6")
            driver.find_element(By.ID, "orbCopyYes").click()
        except NoSuchElementException:
            pass

        driver.find_element(By.ID, "ucPCFooter_btnForward").click()
        print("人数・コピー選択完了")

        try:
            driver.find_element(By.ID, "ucPCFooter_btnForward").click()
            # アラートが出る場合(既に予約済など)をハンドリング
            try:
                WebDriverWait(driver, 3).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                text_ = alert.text
                alert.accept()
                print(f"アラート発生: {text_}")
            except TimeoutException:
                pass

            # PDF保存
            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.join(script_dir, "PDF")
            os.makedirs(base_dir, exist_ok=True)
            now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            pdf_name = f"{user_id}_{now_str}.pdf"
            pdf_path = os.path.join(base_dir, pdf_name)

            settings = {
                'landscape': False,
                'displayHeaderFooter': False,
                'printBackground': True,
                'preferCSSPageSize': True
            }
            pdf_data = driver.execute_cdp_cmd("Page.printToPDF", settings)
            with open(pdf_path, 'wb') as f:
                f.write(base64.b64decode(pdf_data['data']))

            print(f"PDF保存: {pdf_path}")

        except Exception as e:
            print(f"完了処理中にエラー: {e}")

        print(f"→ ユーザー {user_id} の予約完了")

    except Exception as e:
        print(f"例外発生: {e}")

    finally:
        driver.quit()

print("全ユーザーの予約処理が完了しました。")
