import sqlite3
import pandas as pd

# 《《《 建立資料庫 》》》
# 連接stock.db資料庫(若不存在則自動建立一個)
connection = sqlite3.connect('stock_db.db')
# 使用資料庫 cursor 指標進行 SQL 操作
cursor = connection.cursor()
# 執行SQL，新增 stocks 資料表，欄位包含 id(INT)、 name(字串)、closing_price(INT)
cursor.execute(
    '''
    CREATE TABLE IF NOT EXISTS stocks (
            id TEXT PRIMARY KEY NOT NULL,
            name TEXT NOT NULL,
            closing_price INT NOT NULL
    );
    '''
)
# 提交到資料庫執行
connection.commit()

# 《《《 讀取stocks.csv 》》》
# ( 設dtype=object解決「0」被消失的問題 )
df = pd.read_csv('stocks.csv', encoding='utf-8-sig', dtype=object)
# 篩選取得需要的欄位資料
catch_csv = df.loc[:, ['證券代號', '證券名稱', '收盤價']]
# 更換資料欄位名稱
catch_csv.columns = ['id', 'name', 'closing_price']

# 《《《 將csv的資料寫進 DB 》》》
catch_csv.to_sql('stocks', connection, if_exists='append', index=False)

# 《《《 操作sql，從 DB 取得符合條件的資料 》》》
result = cursor.execute(
    '''
    SELECT *
    FROM stocks
    WHERE closing_price > 30;
    '''
)

# 《《《 用迴圈印出每一筆資料 》》》
for res in result:
    print(f'id:{res[0]}, name:{res[1]}, closing_price:{res[2]}')

# 關閉資料庫連線
connection.close()
