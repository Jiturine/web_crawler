import requests
import json
import apikey
import os
def requester(comments: list)->str:

    # 硬编码提示模板
    system_prompt = "角色:你是一个严格的情感分析二进制输出器,需要快速分析输入的评论为正面或负面情感，要求分析到隐含情感部分"

    user_prompt = "对输入内容json格式列表中的每一条评论分析其情感为正面还是负面,分别用1和0表示,其中每条评论以|字符分割，要求输出格式为纯布尔字符串,其位置与输入数组中评论位置一一对应"

    # 构建请求消息
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"{user_prompt}\n\n" + 
                      json.dumps(comments)
        }
    ]

    # 构造请求体
    request_body = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0,
        "max_tokens": 8192, 
        "stream": False
    }

    # 发送API请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {apikey.getkey()}"  # apikey_lql，项目完了我会删除
    }

    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=request_body,  
            timeout=4000  
        )
        response.raise_for_status()
        
        # 解析并返回结果
        return response.json()['choices'][0]['message']['content']
        
    except requests.exceptions.HTTPError as e:
        raise Exception(f"API请求错误: {e.response.status_code} - {e.response.text}")
    except requests.Timeout:
        raise Exception("请求超时，请检查网络连接")
    except Exception as e:
        raise Exception(f"处理失败: {str(e)}")
    
if __name__ == "__main__":
    with open(os.path.dirname(os.path.abspath(__file__))+'/upload/20250427232006.json','r')as f:
        co=json.load(f)["comment_list"]
        lst=[item["comment_content"]for item in co]
        with open('res.txt' ,'w+')as f:
            for i in range(10):
                str='|'.join(lst[i*10:i*10+10])
                print(requester(str),file=f)
                print(str,file=f)
                print("---",file=f)