
### ���� ��test_client.py�����˲鿴����Ŀ¼����ȡ��ѡ�� ������book_detail����Ⱦ����

�������ڱ������еģ�����Ҫ���ڱ����������ݿ�����ʹ�ã������ϵĻ��ڶ�Ӧ�ķ��������ݿ�װӦ�þͿ����ˡ���������**Linuxϵͳ**�ϵĲ�����
```bash
sudo apt update
```
```bash
sudo apt install mysql-server
#���涼��yes
```
���ð�ȫ����
```bash
sudo mysql_secure_installation
#ѡyes��0��Ȼ���������룬ѡyes��yes��yes��no��yes
```
�鿴����״̬
```bash
systemctl status mysql.service
```
�������ݿ�
```bash
sudo mysql -u root -p
#Ȼ������֮ǰ���õ�����
```
ѡ��book_crawler���ݿ�
```bash
use book_crawler;
```
�鿴�Ѿ���ȡ���鼮ID������������
```bash
SELECT book_id, book_name, book_author FROM books;
```
����test_sanic.py��Ȼ����test_client.py��ȡ�����ݺ󣬾Ϳ���ֱ�ӵ� **http://localhost:8000/v1/book/data/<�鼮id>** �������