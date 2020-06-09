from flask import Flask, request
from flask_cors import CORS
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from stocklab.db_handler.mongodb_handler import MongoDBHandler
import datetime

# API 서버의 기본 코드

app = Flask(__name__)
CORS(app)
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
            code_info = {code_hname_to_eng[field]: item[field] for field in item.keys() if field in code_hname_to_eng} # 한글 -> 영문 필드명
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
    def get(self, code):
        pass

class OrderList(Resource):
    def get(self):
        pass

api.add_resource(CodeList, "/codes", endpoint="codes")
api.add_resource(Code, "/codes/<string:code>", endpoint="code")
api.add_resource(Price, "/codes/<string:code>/price", endpoint="price")
api.add_resource(OrderList, "/orders", endpoint="orders")


if __name__ == "__main__":
    app.run(debug=True)