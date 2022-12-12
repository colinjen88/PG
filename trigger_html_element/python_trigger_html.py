from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
# ========================================
# 參數設定
sell_it = 'GEL'
buy_it = 'SCR'
switch_amount = 7
url = 'https://beets.fi/swap'
# ========================================

# webdriver for chrome (https://sites.google.com/a/chromium.org/chromedriver/downloads)
driver = webdriver.Chrome('./chromedriver')    # 指向 chromedriver 的位置
# 要操作的網址
driver.get(url)
sleep(1)
# 交換上下位置 (點擊中間方向鈕)
switch = driver.find_element(By.CSS_SELECTOR, '.css-vn2aq').click()
sleep(1)
# 點擊buy幣種選單
buy_select = driver.find_element(By.CSS_SELECTOR, '.css-1yyxtrm').click()
# 填入buy幣種名稱
buy_name = driver.find_element(By.CSS_SELECTOR, '.css-1t4e6ir')
buy_name.send_keys(buy_it)
sleep(1)
# 確認選擇幣種
buy_choice = driver.find_element(By.CSS_SELECTOR, '.css-jj6esm').click()
sleep(2)

# 交換上下位置 (點擊中間方向鈕)
switch = driver.find_element(By.CSS_SELECTOR, '.css-vn2aq').click()
sleep(2)

# 點擊Sell幣種選單
sell_select = driver.find_element(By.CSS_SELECTOR, '.css-1yyxtrm').click()
# 填入Sell幣種的名稱
sell_name = driver.find_element(By.CSS_SELECTOR, '.css-1t4e6ir')
sell_name.send_keys(sell_it)
sleep(1)
# 確認選擇幣種
sell_choice = driver.find_element(By.CSS_SELECTOR, '.css-jj6esm').click()
sleep(1)

# 填入數量
sell_num = driver.find_element(By.CSS_SELECTOR, '.css-1svuy86')
sleep(1)
# 刪除原本的數字
sell_num.send_keys(Keys.DELETE)
sell_num.send_keys(Keys.DELETE)
sell_num.send_keys(Keys.DELETE)
sell_num.send_keys(Keys.DELETE)
sell_num.send_keys(Keys.DELETE)
sell_num.send_keys(Keys.DELETE)
sell_num.send_keys(Keys.DELETE)
sell_num.send_keys(Keys.DELETE)
sell_num.send_keys(Keys.DELETE)
sell_num.send_keys(Keys.DELETE)
# 填入要交𢰼的數量
sell_num.send_keys(switch_amount)

sleep(1)
# 點擊 [ Connect Wallet ] 按鈕
connect_wallet = driver.find_element(By.CSS_SELECTOR, '.css-1wej8jv').click()


sleep(8)
