from flask import Flask, request
from flask_cors import CORS
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from stocklab.db_handler.mongodb_handler import MongoDBHandler
import datetime

# API 서버의 기본 코드

app = Flask(__name__)
CORS(app) # CORS : 보안 정책과 관련된 사항으로, 요청하는 client와 server의 도메인이나 포트가 다를 때 발생할 수 있다
api = Api(app)

code_hname_to_eng = {
    "단축코드": "code",
    "확장코드": "extend_code",
    "종목명": "name",
    "시장구분": "market",
    "ETF구분": "is_etf",
    "주문수량단위": "memedan",
    "기업인수목적회사구분": "is_spac"
}

price_hname_to_eng = {
    "날짜": "date",
    "종가": "close",
    "시가": "open",
    "고가": "high",
    "저가": "low",
    "전일대비": "diff",
    "전일대비구분": "diff_type"
}

code_fields = {
    "code": fields.String,
    "extend_code": fields.String,
    "name": fields.String,
    "memedan": fields.Integer,
    "market": fields.String,
    "is_etf": fields.String,
    "is_spac": fields.String,
    "uri": fields.Url("code")
}

code_list_short_fields = {
    "code": fields.String,
    "name": fields.String
}
code_list_fields = {
    "count": fields.Integer,
    "code_list": fields.List(fields.Nested(code_fields)),
    "uri": fields.Url("codes")
}

price_fields = {
    "date": fields.Integer,
    "start": fields.Integer,
    "close": fields.Integer,
    "open": fields.Integer,
    "high": fields.Integer,
    "low": fields.Integer,
    "diff": fields.Float,
    "diff_type": fields.Integer
}

price_list_fields = {
    "count": fields.Integer,
    "price_list": fields.List(fields.Nested(price_fields)),
}


mongodb = MongoDBHandler()
# 참조 : https://flask-restful.readthedocs.io/en/0.3.3/intermediate-usage.html#full-parameter-parsing-example

class CodeList(Resource):
    @marshal_with(code_list_fields) # 데코레이터 : 정의된 스키마 이외에 다른 데이터는 반환할 수 없다
    def get(self):
        market = request.args.get('market', default="0", type=str)
        if market == "0": # ALL
            results = list(mongodb.find_items({}, "stocklab", "code_info"))
        elif market == "1" or market == "2": # 1(코스피), 2(코스닥)
            results = list(mongodb.find_items({"시장구분": market}, "stocklab", "code_info"))
        result_list = []
        for item in results:
            code_info = {}
            code_info = {code_hname_to_eng[field]: item[field] for field in item.keys() if field in code_hname_to_eng} # 한글 필드명 -> 영문
            result_list.append(code_info)
        return {"code_list": result_list, "count": len(result_list)}, 200

class Code(Resource):
    @marshal_with(code_fields)
    def get(self, code):
        result = mongodb.find_item({"단축코드":code}, "stocklab", "code_info")
        if result is None:
            return {}, 404
        code_info = {}
        code_info = {code_hname_to_eng[field]: result[field] for field in result.keys() if field in code_hname_to_eng}
        return code_info

class Price(Resource):
    @marshal_with(price_list_fields) # 한글 필드명 -> 영문
    def get(self, code):
        today = datetime.datetime.now().strftime("%Y%m%d")
        default_start_date = datetime.datetime.now() - datetime.timedelta(days=7)
        start_date = request.args.get('start_date', default=default_start_date.strftime("%Y%m%d"), type=str)
        end_date = request.args.get('end_date', default=today, type=str)
        results = list(mongodb.find_items({"code": code, "날짜": {"$gte": start_date, "$lte": end_date}},
                                          "stocklab", "price_info"))
        result_object = {}
        price_info_list = []
        for item in results:
            price_info = {price_hname_to_eng[field]: item[field] for field in item.keys() if field in price_hname_to_eng} # 한글 필드명 -> 영문
            price_info_list.append(price_info)
        result_object["price_list"] = price_info_list
        result_object["count"] = len(price_info_list)
        return result_object, 200

class OrderList(Resource):
    def get(self):
        status = request.args.get('status', default="all", type=str)
        if status == 'all':
            result_list = list(mongodb.find_items({}, "stocklab_demo", "order"))
        elif status in ["buy_ordered", "buy_completed", "sell_ordered", "sell_completed"]:
            result_list = list(mongodb.find_items({"status": status}, "stocklab_demo", "order"))
        else:
            return {}, 404
        return {"count": len(result_list), "order_list": result_list}, 200

api.add_resource(CodeList, "/codes", endpoint="codes")
api.add_resource(Code, "/codes/<string:code>", endpoint="code")
api.add_resource(Price, "/codes/<string:code>/price", endpoint="price")
api.add_resource(OrderList, "/orders", endpoint="orders")


if __name__ == "__main__":
    app.run(debug=True)