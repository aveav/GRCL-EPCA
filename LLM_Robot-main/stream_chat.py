from llama_cpp import Llama

def handle_stream_output(output):
    """
    处理流式输出，将生成的内容逐步打印出来，并收集完整的回复。

    参数：
        output: 生成器对象，来自 create_chat_completion 的流式输出

    返回：
        response: 完整的回复文本
    """
    response = ""
    for chunk in output:
        delta = chunk['choices'][0]['delta']
        if 'role' in delta:
            print(f"{delta['role']}: ", end='', flush=True)
        elif 'content' in delta:
            content = delta['content']
            print(content, end='', flush=True)
            response += content
    return response

class ChatSession:
    def __init__(self, llm):
        self.llm = llm
        self.messages = []

    def add_message(self, role, content):
        """
        添加一条消息到会话中。

        参数：
            role: 消息角色，通常为 'user' 或 'assistant'
            content: 消息内容
        """
        self.messages.append({"role": role, "content": content})

    def get_response_stream(self, user_input):
        """
        获取模型对用户输入的响应（流式输出）。

        参数：
            user_input: 用户输入的文本

        返回：
            response: 完整的回复文本
        """
        self.add_message("user", user_input)
        
        try:
            output = self.llm.create_chat_completion(
                messages=self.messages,
                stream=True  # 开启流式输出
            )
            
            response = handle_stream_output(output)  # 同时打印和收集回复
            
            self.add_message("assistant", response.strip())
            return response.strip()
        except Exception as e:
            print(f"\n发生错误: {e}")
            return ""

# 初始化模型（假设使用本地路径）
model_path = "./models/llama/gemma-2-9b-it-Q6_K.gguf"
llm = Llama(
    n_ctx=4096,
    model_path=model_path,
    n_gpu_layers=-1,  # 根据需要卸载到 GPU
    verbose=False,    # 禁用详细日志输出
)

# 创建会话实例
chat = ChatSession(llm)
        
# 开始对话
while True:
    prompt = input("User: ")
    # 退出对话条件（当然，你也可以直接终止代码块）
    if prompt.lower() in ["exit", "quit", "bye"]:
        print("Goodbye!")
        break
    chat.get_response_stream(prompt)
    print()  # 换行以便下一次输入，这是因为之前的 print 都设置了 end=''

