### 修bug，暂时注释掉了情感注释部分

### 更新 此区域划分为本地测试 本地运行test_sanic.py即可测试

### 更新 前端优化+超时处理+鸽注册登录系统+动态获取headers

### 更新 在test_client.py更新了查看已爬目录和爬取的选择 增加了book_detail的渲染内容
### 更新 将book_crawler 改为 web_crawler，增加影评数据表

### 期望在云服务器也安装mysql数据库

## **Linux系统**安装**mysql**数据库：
```bash
sudo apt update
```
```bash
sudo apt install mysql-server
#后面都填yes
```
- **配置安全设置**
```bash
sudo mysql_secure_installation
#选yes，0，然后设置密码，选yes，yes，yes，no，yes
```
- **查看运行状态**
```bash
systemctl status mysql.service
```
- **启动数据库**
```bash
sudo mysql -u root -p
#然后输入之前设置的密码
```
- **选择web_crawler数据库**
```bash
use web_crawler;
```
- **书籍爬取结果查看**   
查看已经爬取的书籍ID，书名，作者
```bash
SELECT book_id, book_name, book_author FROM books;
```
- **电影爬取结果查看**  
pass
## 测试 
- **本地测试**：  
  运行test_sanic.py，然后在test_client.py爬取到数据。
    - **书籍爬取结果**：**http://localhost:8000/v1/book/data/<书籍id>**
    - **电影爬取结果**：**http://localhost:8000/v1/movie/data/<电影id>**
- **云服务器**：  
    pass
