"""
函數定義區塊
"""
# 設迴圈,捕捉錯誤的輸入格式


def catch_wrong(func):
    def wrap():
        isok = False
        while isok == False:
            print('_'*40)
            print('-'*40)
            the_number = float(input('驗算能否被2整除，請輸入一個整數值：'))
            print('-'*40)
            # 檢查輸入是否為正整數
            isok = func(the_number)
        return the_number
    return wrap
# 驗證輸入的是否為整數(語法糖)


@catch_wrong
def check_int(int_num):
    isok = int_num % 1 == 0
    # 輸入錯誤提示
    if isok == False:
        print('《《《 輸入錯誤，只能輸入整數 》》》')
        print('')
    return isok

# 計算是否被2整除


def division_2(num):
    result = num % 2
    return result


"""
程式執行區塊
"""
# 執行驗證
the_number = check_int()

# 已通過格式檢查。接著進行2整除計算。
divisible = division_2(the_number)
# 去除小數點
the_number = int(the_number)
if divisible == 0:
    print('可以。您輸入的數字 [ ' + str(the_number) + ' ] 可以被2整除。')
else:
    print('Oops! 您輸入的數字 [ ' + str(the_number) + ' ] 無法被2整除。')
