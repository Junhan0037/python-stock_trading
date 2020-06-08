import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from stocklab.agent.ebest import EBest
from stocklab.db_handler.mongodb_handler import MongoDBHandler
from multiprocessing import Process

ebest_demo = EBest("DEMO")
ebest_demo.login()
mongo = MongoDBHandler()

def run_process_trading_scenario(code_list):
    p = Process(target=trading_scenario, args=(code_list,)) # trading_scenario 수행하는 프로세스
    p.start()
    p.join() # 해당 프로레스가 끝날때까지 기다린다
    print("run process join")

def check_buy_completed_order(code): # 매수완료된 주문은 매도 주문
    # 매도완료 데이터를 가져온다
    buy_completed_order_list = list(mongo.find_items({"$and":[
                                                {"code": code},
                                                {"status": "buy_completed"}
                                            ]},
                                                "stocklab_demo", "order"))

    # 가져온 항목에 대해서 수량만큼 +10호가로 매도주문
    for buy_completed_order in buy_completed_order_list:
        buy_price = buy_completed_order["매수완료"]["주문가격"]
        buy_order_no = buy_completed_order["매수완료"]["주문번호"]
        tick_size = ebest_demo.get_tick_size(int(buy_price))
        print("tick_size", tick_size)
        sell_price = int(buy_price) + tick_size*10
        sell_order = ebest_demo.order_stock(code, "2", str(sell_price), "1", "00")
        print("order_stock", sell_order)
        mongo.update_item({"매수완료.주문번호": buy_order_no},
                          {"$set": {"매도주문": sell_order[0], "status": "sell_ordered"}},
                          "stocklab_demo", "order")
        
def check_buy_order(code): # 매수주문 완료 체크
    # 결과(order_list)에 대해 order_check 메서드를 이용해 체결 수량이 주문 수량과 동일한지 확인하고, 같으면 매수완료로 MongoDB에 해당 주문에 대한 정보를 업데이트
    order_list = list(mongo.find_items({"$and":[
                                            {"code": code}, 
                                            {"status":"buy_ordered"}]
                                        }, 
                                        "stocklab_demo", "order"))
    for order in order_list:
        time.sleep(1)
        code = order["code"]
        order_no = order["매수주문"]["주문번호"]
        order_cnt = order["매수주문"]["실물주문수량"]
        check_result = ebest_demo.order_check(order_no)
        print("check buy order result", check_result)
        result_cnt = check_result["체결수량"]
        if order_cnt == result_cnt:
            mongo.update_item({"매수주문.주문번호":order_no}, {"$set":{"매수완료":check_result, "status":"buy_completed"}}, "stocklab_demo", "order")
            print("매수완료", check_result)
    return len(order_list)

def check_sell_order(code): # 매도주문이 수량만큼 체결됐는지 확인하고, 체결됐다면 매도 완료로 채결 정보를 저장
    # 매도주문 데이터를 가져온다
    sell_order_list = list(mongo.find_items({"$and":[
                                            {"code": code}, 
                                            {"status": "sell_ordered"}
                                        ]}, 
                                            "stocklab_demo", "order"))
    # order_check를 이용해 체결 수량을 확인하고 업데이트
    for order in sell_order_list:
        time.sleep(1)
        code = order["code"]
        order_no = order["매도주문"]["주문번호"]
        order_cnt = order["매도주문"]["실물주문수량"]
        check_result = ebest_demo.order_check(order_no)
        print("check sell order result", check_result)
        result_cnt = check_result["체결수량"]
        if order_cnt == result_cnt:
            mongo.update_item({"매도주문.주문번호":order_no}, 
                            {"$set":{"매도완료":check_result, "status":"sell_completed"}}, 
                            "stocklab_demo", "order")
            print("매도완료", check_result)
    return len(sell_order_list)

def trading_scenario(code_list):
    for code in code_list:
        time.sleep(1)
        print(code)
        result = ebest_demo.get_current_call_price_by_code(code) # 현재 호가 확인
        current_price = result[0]["현재가"]
        print("current_price", current_price)
        """매수주문 체결확인
        """
        buy_order_cnt = check_buy_order(code) # 현재 매수 주문의 상태 체크, 수량을 돌려받는다
        check_buy_completed_order(code) # 매수 완료된 주문에 대해서 +10호가로 매도 주문
        if buy_order_cnt == 0: # 매수 주문의 수량이 0이면 현재가에 매수 주문
            order = ebest_demo.order_stock(code, "2", current_price, "2", "00")
            print("order_stock", order)
            order_doc = order[0]
            mongo.insert_item({"매수주문":order_doc, "code":code, "status": "buy_ordered"}, "stocklab_demo", "order") # 매수 주문 저장
        check_sell_order(code) # 매도 주문에 대한 상태 체크

if __name__ == '__main__':
    scheduler = BackgroundScheduler() # 실행에 필요한 함수는 프로세스를 생성해 실행
    day = datetime.now() - timedelta(days=4)
    today = day.strftime("%Y%m%d")
    code_list = ["180640", "005930", "091990"] # 종목 코드
    print("today:", today)
    scheduler.add_job(func=run_process_trading_scenario,
        trigger="interval", minutes=5, id="demo",
        kwargs={"code_list":code_list})
    scheduler.start()
    while True:
        print("waiting...", datetime.now())
        time.sleep(1)

# 참고 : 미채결 주문에 대한 관리는 별도로 하지 않는다.