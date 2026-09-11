from fastapi import FastAPI
from pydantic import BaseModel
#1.开店：创建应用实例
app = FastAPI()

#1.定义一张“点单小票”的规范模板
class OrderItem(BaseModel):
    item_name:str #必须是字符串（比如“珍珠奶茶”）
    quantity:int #必须是整数（比如2）

#2.挂出第一个收银窗口(GET请求)
@app.get("/hello")
def say_hello():
    return {"message":"你好！这是我的第一个FastAPI接口！"}

#3.新建一个“收银点单”窗口（用POST，因为顾客要往里递交数据）
@app.post("/order")
def make_order(order:OrderItem):
    #这里函数直接拿到了通过质检的数据：order.item_name和order.quantity
    total_price = order.quantity *15
    return {
        "status":"下单成功",
        "detail":f"你点了{order.quantity}杯{order.item_name}",
        "total_cost":total_price,
    }
