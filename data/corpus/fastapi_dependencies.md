# FastAPI 依赖注入机制

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 声明依赖
用 Depends 声明路径操作所需的依赖。FastAPI 在调用路径操作时执行依赖函数，把请求数据提供给依赖，并把依赖返回值注入路径操作参数。依赖函数本身无需先被手动调用再传给 Depends。

来源：https://fastapi.tiangolo.com/tutorial/dependencies/

## 2. 共享依赖与类型别名
多个路径操作可以复用同一个依赖。可使用 Annotated 配合 Depends 声明依赖参数，再将该 Annotated 类型表达式保存为类型别名；这种普通 Python 别名减少重复声明，并保留类型信息和编辑器支持。

来源：https://fastapi.tiangolo.com/tutorial/dependencies/

## 3. 同步和异步依赖
依赖函数既可写成普通 def，也可写成 async def。FastAPI 允许同步路径操作使用异步依赖，也允许异步路径操作使用同步依赖，由框架按相应调用方式处理；不要求路径操作与依赖的声明形式相同。

来源：https://fastapi.tiangolo.com/tutorial/dependencies/
