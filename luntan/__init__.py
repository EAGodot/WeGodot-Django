#來自deepseek的關於mysqlclient安裝失敗的解決方案
# 在 myproject/__init__.py 文件中添加：
import pymysql
pymysql.install_as_MySQLdb()