from datetime import datetime
import time
from stocklab.agent.ebest import EBest
from stocklab.db_handler.mongodb_handler import MongoDBHandler

"""
윈도우 스케줄러
"""

# 데이터 수집 실행
mongodb = MongoDBHandler()
ebest = EBest("DEMO")
ebest.login()

def collect_code_list(): # 종목 코드를 수집하는 메서드
    result = ebest.get_code_list("ALL")
    mongodb.delete_items({}, "stocklab", "code_info")
    mongodb.insert_items(result, "stocklab", "code_info")

def collect_stock_info(): # 주식 가격을 수집하는 메서드
    code_list = mongodb.find_items({}, "stocklab", "code_info")
    target_code = set([item["단축코드"] for item in code_list])
    today = datetime.today().strftime("%Y%m%d")
    collect_list = mongodb.find_items({"날짜": today}, "stocklab", "price_info").distinct("code")
    for col in collect_list:
        target_code.remove(col) # 오늘 날짜로 수집된 데이터가 있다면 제외시킨다. 데이터 중복을 방지.

    for code in target_code:
        result_price = ebest.get_stock_price_by_code(code, "1") # 1일 치 데이터 수집
        time.sleep(1)
        if len(result_price) > 0:
            mongodb.insert_items(result_price, "stocklab", "price_info")

if __name__ == '__main__':
    collect_code_list()
    collect_stock_info()