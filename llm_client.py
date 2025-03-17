from openai import OpenAI
API_BASE_URL = "http://localhost:3000/v1"
API_KEY = "sk-cOTdKVNuhsGFvpus426c073842244e15B536D1BcCf7fC567"

class LLMClient:
    def __init__(self, api_key=API_KEY, base_url=API_BASE_URL):
        """初始化LLM客户端"""
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
    def chat(self, messages, model="deepseek-ai/DeepSeek-R1-Distill-Qwen-14B"):
        """与LLM交互
        
        Args:
            messages: 消息列表
            model: 使用的LLM模型
        
        Returns:
            tuple: (content, reasoning_content)
        """
        try:
            print(f"LLM请求: {messages}")
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
            )
            if response.choices:
                message = response.choices[0].message
                content = getattr(message, "content", "")
                reasoning_content = getattr(message, "reasoning_content", "")
                print(f"Output: {content}")
                return content, reasoning_content
            
            return "", ""
                
        except Exception as e:
            print(f"LLM调用出错: {str(e)}")
            return "", ""

# 使用示例
if __name__ == "__main__":
    llm = LLMClient()
    messages = [
        {"role": "user", "content": "你好"}
    ]
    response = llm.chat(messages)
    print(f"响应: {response}")