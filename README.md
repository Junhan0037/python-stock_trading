# python-stock_trading

주식 자동 거래 API


### 주식 거래 시스템의 API 디자인

| 자원 | URL | GET |
|------|---------------|-------------|
| 주식종목 리스트 (CodeList) | /codes | 모든 주식 종목 코드를 조회
| 개별 종목 (Code) | /codes/{code} | {code} 종목 코드의 정보를 조회
| 개별 종목 가격 (Price) | /codes/{code}/price | {code} 종목 코드의 가격 정보를 조회
| 주문 리스트 (OrderList) | /orders | 모든 주문 정보 조회
| 개별 주문 (Order) | /orders/{id} | 개별 주문 정보 조회
