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

# 1. 大沼公園グラウンドを含むテーブルを見つける
onuma_table = wait.until(EC.presence_of_element_located((
    By.XPATH, "//span[text()='大沼公園グラウンド']/ancestor::table[not(contains(@id, 'TdSideMenu'))]"
)))
# onuma_table = wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='大沼公園グラウンド']/ancestor::table")))
if onuma_table:
      print("onuma_table:")
      print(onuma_table)
else:
     print("onuma_tableは無い")


rows=onuma_table.find_elements(By.TAG_NAME,"tr")

target_text="水"
column_index=-1

for row in rows:
    index = 0  # セルのインデックス
    # その行にtarget_textが含まれるか確認
    if row.find_elements(By.XPATH,f".//td[contains(text(),'{target_text}')]"):
        print("この行に含まれています")
        # target_textが含まれている場合、各セルを確認して何列目にtarget_textがあるか判定
        cells = row.find_elements(By.XPATH, ".//td")
        

        for cell in cells:
             if target_text in cell.text:
                  print(f"この行の{index+1}列目に{target_text}が含まれてます")
                  break #target_textを見つけたので処理終了
             
             index+=1 #見つけない場合、indexを1つ増やす
    else:
        # target_textが見つからなかった場合、1列目のセルのtextを出力
        first_cell = row.find_element(By.XPATH, ".//td[1]")  # 1列目のセル
        print(f"1列目のセルの内容: {first_cell.text}")
        print(f"この行に{target_text}は含まれていません")
print(f"index:{index}")         

# 3ヶ月後の1日から順番に見ていき、最初に該当の曜日があるか確認。何日かと、それが何曜日かを取得

    # columns = row.find_elements(By.TAG_NAME, "td")  # 各行のすべての列を取得
#     for index, column in enumerate(columns):
#         #水がその行に含まれているか確認。含まれている時だけ、その後の処理を進める
#         #  
#         column_index = column_index + 1  
#         if target_text in column.text:  # 指定の文字が含まれているかチェック
#             # column_index = column_index + 1  # 列番号を1から始まるように設定
#             break
#     # if column_index != -1:
#         break  # 目的の列を見つけたらループを終了

# if column_index != -1:
#     print(f"文字 '{target_text}' が含まれる列番号: {column_index}")
# else:
#     print(f"文字 '{target_text}' が含まれる列は見つかりませんでした。")







# # テーブル全体の構造を出力して確認
# print(onuma_table.get_attribute('outerHTML'))
# # 2. そのテーブルの中で"火"が含まれるセルを見つける
# fire_cells = onuma_table.find_elements(By.XPATH, ".//td[contains(text(), '火')]")
# if not fire_cells:
#     print("No cells found with '火'.")
# else:
#     print(f"Found {len(fire_cells)} cells with '火'.")

# # そのセルが左から何番目かを配列に格納する
# fire_indices = []
# for cell in fire_cells:
#     parent_row = cell.find_element(By.XPATH, "..")  # 親の行を取得
#     all_cells = parent_row.find_elements(By.XPATH, "./td")  # 行内の全セルを取得
#     for index, each_cell in enumerate(all_cells):
#         if each_cell == cell:
#             fire_indices.append(index + 1)  # 1-based index

# print(f"Indices of '火' cells: {fire_indices}")

# # 3. "抽選"が書かれた行内で、2.で記憶している列の要素をクリック
# for index in fire_indices:
#     try:
#         draw_cell = onuma_table.find_element(By.XPATH, f".//tr[contains(@style,'background-color:White')]/td[{index}]/a[contains(text(), '抽選')]")
#         if draw_cell:
#             draw_cell.click()
#             print(f"Clicked draw cell at index {index}")
#             break
#     except Exception as e:
#         print(f"Error clicking draw cell at index {index}: {e}")


while True:
    pass