
### 更新 在test_client.py更新了查看已爬目录和爬取的选择 增加了book_detail的渲染内容

由于是在本地运行的，所以要先在本地运行数据库后才能使用，在云上的话在对应的服务器数据库装应该就可以了。下面是在**Linux系统**上的操作：
```bash
sudo apt update
```
```bash
sudo apt install mysql-server
#后面都填yes
```
配置安全设置
```bash
sudo mysql_secure_installation
#选yes，0，然后设置密码，选yes，yes，yes，no，yes
```
查看运行状态
```bash
systemctl status mysql.service
```
启动数据库
```bash
sudo mysql -u root -p
#然后输入之前设置的密码
```
选择book_crawler数据库
```bash
use book_crawler;
```
查看已经爬取的书籍ID，书名，作者
```bash
SELECT book_id, book_name, book_author FROM books;
```
运行test_sanic.py，然后在test_client.py爬取到数据后，就可以直接到 **http://localhost:8000/v1/book/data/<书籍id>** 来看结果