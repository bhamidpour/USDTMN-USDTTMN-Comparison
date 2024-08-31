import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
import schedule

# ایجاد یک فایل اکسل با سه ستون: قیمت تتر، قیمت دلار، و اختلاف دو قیمت
excel_file = 'prices.xlsx'

# بررسی اینکه آیا فایل از قبل وجود دارد یا نه، اگر وجود ندارد آن را ایجاد کنید
try:
    df = pd.read_excel(excel_file)
except FileNotFoundError:
    df = pd.DataFrame(columns=['Timestamp', 'Tether Price', 'Dollar Price', 'Price Difference'])
    df.to_excel(excel_file, index=False)

# تابع برای دریافت قیمت تتر از سایت تترلند
def get_tether_price():
    url = 'https://arzdigital.com/coins/tether/'
    headers = {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    # استخراج قیمت تتر
    price = soup.find('span', {'class': 'pulser-toman-tether'}).text.strip()
    price = price.replace('تومان', '').strip()  # حذف کلمه "تومان"
    price = convert_to_english_number(price)  # تبدیل اعداد فارسی به انگلیسی
    print(f"Tether price retrieved: {price}")
    return float(price.replace(',', ''))

def convert_to_english_number(persian_str):
    persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
    english_numbers = '0123456789'
    translation_table = str.maketrans(persian_numbers, english_numbers)
    return persian_str.translate(translation_table)

# تابع برای دریافت قیمت دلار از سایت بن بست
def get_dollar_price():
    #url = 'https://www.tgju.org/profile/price_dollar_rl'
    url = 'https://www.tgju.org/%D9%82%DB%8C%D9%85%D8%AA-%D8%AF%D9%84%D8%A7%D8%B1'
    headers = {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    # استخراج قیمت دلار
    #price = soup.find('span', {'data-col': 'info.last_trade.PDrCotVal'}).text.strip()
    #print(f"Dollar price retrieved: {price}")

    row = soup.find('tr', {'data-market-nameslug': 'price_dollar_rl'})
    if row:
        price_element = row.find('td', class_='nf')
        if price_element:
            price = price_element.text.strip().replace(',', '')
            price = float(price)
            print(f"Dollar price retrieved: {price}")

    return float(price)/10 #convert to toman

# تابع برای ثبت قیمت‌ها در فایل اکسل
def record_prices():
    dollar_price = get_dollar_price()
    tether_price = get_tether_price()
    price_difference = tether_price - dollar_price

# اضافه کردن داده‌ها به فایل اکسل
    df = pd.read_excel(excel_file)
    new_row = pd.DataFrame({'Timestamp': [datetime.now()], 
                            'Tether Price': [tether_price], 
                            'Dollar Price': [dollar_price], 
                            'Price Difference': [price_difference]})
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(excel_file, index=False)
    print(f"Prices recorded: Tether: {tether_price}, Dollar: {dollar_price}, Difference: {price_difference}")

# تابع برای چک کردن شرایط خرید
def check_conditions():
    df = pd.read_excel(excel_file)
    last_three_days = df[df['Timestamp'] > datetime.now() - timedelta(days=3)]
    negative_diff = last_three_days[last_three_days['Price Difference'] < 0]

    if len(negative_diff) > 0.95 * len(last_three_days):
        print("امروز وقت خریده")
    else:
        print("عجله نکن!")

# زمان‌بندی ثبت قیمت‌ها هر 5 دقیقه
schedule.every(30).seconds.do(record_prices)
print("get Price task started...")

# زمان‌بندی چک کردن شرایط خرید هر 12 ساعت
schedule.every(12).hours.do(check_conditions)
print("check Condition task started...")

# حلقه اصلی برای اجرا
while True:
    schedule.run_pending()
    time.sleep(1)
