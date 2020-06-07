import time
import inspect
from multiprocessing import Process
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from stocklab.agent.ebest import EBest
from stocklab.agent.data import Data
from stocklab.db_handler.mongodb_handler import MongoDBHandler

"""
파이썬 스케줄러
"""

def run_process_collect_code_list():
    print(inspect.stack()[0][3])
    p = Process(target=collect_code_list())
    p.start() # 각 프로세스는 개별로 동작
    p.join() # 자식 프로세스의 종료를 가다리는 방법

def run_process_collect_stock_info():
    print(inspect.stack()[0][3])
    p = Process(target=collect_stock_info)
    p.start()
    p.join()

def collect_code_list(): # 종목 코드를 수집하는 메서드
    ebest = EBest("DEMO")
    mongodb = MongoDBHandler()
    ebest.login()
    result = ebest.get_code_list("ALL")
    mongodb.delete_items({}, "stocklab", "code_info")
    mongodb.insert_items(result, "stocklab", "code_info")

def collect_stock_info(): # 주식 가격을 수집하는 메서드
    ebest = EBest("DEMO")
    mongodb = MongoDBHandler()
    ebest.login()
    code_list = mongodb.find_items({}, "stocklab", "code_info")
    target_code = set([item["단축코드"] for item in code_list])
    today = datetime.today().strftime("%Y%m%d")
    print(today)
    collect_list = mongodb.find_items({"날짜": today}, "stocklab", "price_info").distinct("code")
    for col in collect_list:
        target_code.remove(col) # 오늘 날짜로 수집된 데이터가 있다면 제외시킨다. 데이터 중복을 방지.
    for code in target_code:
        time.sleep(1)
        print("code:", code)
        result_price = ebest.get_stock_price_by_code(code, "1") # 1일 치 데이터 수집
        if len(result_price) > 0:
            print(result_price)
            mongodb.insert_items(result_price, "stocklab", "price_info")

        result_credit = ebest.get_credit_trend_by_code(code, today)
        if len(result_credit) > 0:
            mongodb.insert_items(result_credit, "stocklab", "credit_info")

        result_short = ebest.get_short_trend_by_code(code, sdate=today, edate=today)
        if len(result_short) > 0:
            mongodb.insert_items(result_short, "stocklab", "short_info")

        result_agent = ebest.get_agent_trend_by_code(code, fromdt=today, todt=today)
        if len(result_agent) > 0:
            mongodb.insert_items(result_agent, "stocklab", "agent_info")

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=run_process_collect_code_list, trigger="cron",
                      day_of_week="mon-fri", hour="19", minute="00", id="1")
    scheduler.add_job(func=run_process_collect_stock_info, trigger="cron",
                      day_of_week="mon-fri", hour="19", minute="05", id="2")
    scheduler.start()
    while True:
        print("running", datetime.now())
        time.sleep(1)