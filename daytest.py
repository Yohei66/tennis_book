import datetime
from dateutil.relativedelta import relativedelta

# 対象の曜日 (0: Monday, 1: Tuesday, 2: Wednesday, 3: Thursday, 4: Friday, 5: Saturday, 6: Sunday)
target_weekdays = [1, 3, 5]  # 火:1, 木:3, 土:5

# 曜日の日本語表記
japanese_weekdays = ["月", "火", "水", "木", "金", "土", "日"]

# 今日の日付を取得
today = datetime.date.today()

# 3か月後の1日
three_months_later = today + relativedelta(months=4)
first_day_of_next_3months = three_months_later.replace(day=1)

# 3か月後の1日から開始して、該当する曜日を見つける
current_day = first_day_of_next_3months
while current_day.weekday() not in target_weekdays:
    current_day += datetime.timedelta(days=1)

# 曜日を日本語の省略表記で取得
weekday_jp = japanese_weekdays[current_day.weekday()]

# 結果を表示
print(f"3か月後の1日以降、最初に該当するのは {current_day} ({weekday_jp}) です。")



import datetime

# 指定された年と月の火曜日を取得する関数
def get_tuesdays_of_specific_month(year, month):
    # 指定された年と月の最初の日付を取得
    first_day_of_month = datetime.date(year, month, 1)
    # 最初の火曜日を見つける
    days_ahead = (1 - first_day_of_month.weekday()) % 7  # 1は火曜日
    first_tuesday = first_day_of_month + datetime.timedelta(days=days_ahead)
    
    # 指定された月内の毎週火曜日を取得
    tuesdays = []
    current_tuesday = first_tuesday
    while current_tuesday.month == month:
        tuesdays.append(current_tuesday)
        current_tuesday += datetime.timedelta(weeks=1)
    
    return tuesdays

# 3か月後の月の火曜日を取得する関数
def get_tuesdays_of_next_3_months_later():
    today = datetime.date.today()
    # 3ヶ月後の日付を計算し、その月と年を取得
    three_months_later = today.replace(day=1) + datetime.timedelta(days=120)
    year = three_months_later.year
    month = three_months_later.month
    
    return get_tuesdays_of_specific_month(year, month)

# 3か月後の火曜日を取得
tuesdays_in_three_months = get_tuesdays_of_next_3_months_later()

# 結果を表示
for tuesday in tuesdays_in_three_months:
    print(tuesday)


print('----------')
import datetime
import holidays

# 指定された年と月の全ての指定曜日の日付を取得する関数
def get_all_weekdays_of_month(year, month, weekdays):
    """
    year: 年
    month: 月
    weekdays: 曜日リスト (0=月曜日, 1=火曜日, ..., 6=日曜日)
    """
    first_day_of_month = datetime.date(year, month, 1)
    last_day_of_month = (first_day_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

    weekdays_dates = []
    for weekday in weekdays:
        # 最初の指定曜日を見つける
        days_ahead = (weekday - first_day_of_month.weekday()) % 7
        first_weekday = first_day_of_month + datetime.timedelta(days=days_ahead)

        # 月内の指定曜日の日付を取得
        current_weekday = first_weekday
        while current_weekday <= last_day_of_month:
            weekdays_dates.append(current_weekday)
            current_weekday += datetime.timedelta(weeks=1)
    
    return weekdays_dates

# 日本の祝日を取得する関数
def get_japanese_holidays_of_month(year, month):
    jp_holidays = holidays.Japan(years=[year])
    month_holidays = []
    for date in jp_holidays:
        if date.year == year and date.month == month:
            month_holidays.append(date)
    return month_holidays

# 3か月後の指定曜日（複数）と祝日を取得する関数
def get_weekdays_and_holidays_of_next_3_months_later(weekdays):
    today = datetime.date.today()
    # 3ヶ月後の月の初日を取得
    three_months_later = today.replace(day=1) + datetime.timedelta(days=120)
    year = three_months_later.year
    month = three_months_later.month
    
    # 指定された月の曜日に該当する日付を取得
    weekdays_dates = get_all_weekdays_of_month(year, month, weekdays)
    
    # 指定された月の日本の祝日を取得
    holidays = get_japanese_holidays_of_month(year, month)
    
    # 曜日の日付と祝日の日付を結合し、重複を排除
    all_dates = sorted(set(weekdays_dates + holidays))
    
    return all_dates

# 日付をYYYYMMDD形式で返す関数
def format_dates_to_yyyymmdd(dates):
    return [date.strftime('%Y%m%d') for date in dates]

# 火曜日(1)と木曜日(3)を指定して3か月後のそれらの日付と祝日を取得
weekdays = [1, 3]  # 0=月曜日, 1=火曜日, 2=水曜日, ..., 6=日曜日
dates_in_three_months = get_weekdays_and_holidays_of_next_3_months_later(weekdays)

# 結果をYYYYMMDD形式で表示
formatted_dates = format_dates_to_yyyymmdd(dates_in_three_months)
for date in formatted_dates:
    print(date)


