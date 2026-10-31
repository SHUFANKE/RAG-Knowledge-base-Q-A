# FastAPI Bearer 令牌与 JWT

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 提取 Bearer 令牌
OAuth2PasswordBearer 作为依赖时，从 Authorization 请求头提取 Bearer 后的令牌字符串。该工具提取令牌并描述 OpenAPI 安全方案；提取字符串本身不等于完成用户身份或 JWT 签名验证。

来源：https://fastapi.tiangolo.com/tutorial/security/first-steps/

## 2. 缺少令牌
在官方默认用法中，缺少 Authorization 请求头或请求头不是 Bearer 令牌形式时，OAuth2PasswordBearer 直接返回 HTTP 401 未授权错误。该行为描述默认配置，不覆盖显式改变自动错误处理的情况。

来源：https://fastapi.tiangolo.com/tutorial/security/first-steps/

## 3. JWT 签名与加密
JWT 可以将 JSON 对象编码为紧凑令牌。官方教程强调示例 JWT 经过签名，但没有加密，持有人可以恢复其内容。签名用于验证令牌来源，不能把敏感数据放进去并期待签名使内容保密。

来源：https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
