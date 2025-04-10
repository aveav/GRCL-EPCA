import json
import re
from abc import ABC, abstractmethod
import requests

class BaseLLM(ABC):
    def __init__(self, model_name: str):
        """
        基类的构造函数，确保所有子类都必须提供 model_name
        """
        self.model_name = model_name

    @abstractmethod
    def create_chat_completion(self, messages):
        pass

    @abstractmethod
    def get_model_info(self):
        pass


class LlamaLLM(BaseLLM):
    def __init__(self, model_name = "./models/llama/gemma-2-9b-it-Q6_K.gguf", n_ctx=4096, chat_format="chatml", n_gpu_layers=-1):
        from llama_cpp import Llama
        self.model = Llama(model_path=model_name, n_ctx=n_ctx, chat_format=chat_format, n_gpu_layers=n_gpu_layers)

    def create_chat_completion(self, messages):
        return self.model.create_chat_completion(messages=messages)['choices'][0]['message']['content']

    def get_model_info(self):
        return f"Llama model at {self.model.model_name}"
    

class OllamaLLM(BaseLLM):
    def __init__(self, model_name = 'qwen2.5-coder:32b'):
        #工作空间在huxy文件夹下，不知道为啥
        self.model_name = model_name

    def create_chat_completion(self, messages):
        from ollama import chat
        return chat(self.model_name,messages=messages)['message']['content']

    def get_model_info(self):
        return f"OLlama model{self.model_name}"

class APILLM(BaseLLM):
    def __init__(self, model_name="gpt-4o", api_url="https://api.cxhao.com/v1/chat/completions", api_key="sk-FZwRGbVq8YbbFQVRA4Cf69246367496a9f9363D7746477A2"):
        """
        APILLM class to interact with an external API.
        :param model_name: The name of the model (default: "gpt-4o").
        :param api_url: The URL of the API endpoint.
        :param api_key: The API key for authentication.
        """
        self.model_name = model_name
        self.api_url = api_url
        self.api_key = api_key

    def create_chat_completion(self, messages):
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }
        
        payload = json.dumps({
            "model": self.model_name,
            "messages": messages
        })

        response = requests.post(self.api_url, headers=headers, data=payload)

        # Check if the response is successful
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            response.raise_for_status()

    def get_model_info(self):
        return f"APILLM model: {self.model_name}"

class LLMFactory:
    @staticmethod
    def create_llm(model_type, model_name=None, **kwargs):
        model_map = {
            "llama": LlamaLLM,
            "ollama": OllamaLLM,
            "api":APILLM,
            # 以后添加新模型时，只需要在这里添加映射即可
        }

        # 获取对应的 LLM 类
        model_class = model_map.get(model_type)

        if not model_class:
            raise ValueError(f"Unsupported model type: {model_type}")

        # 如果没有传递 model_name，则使用默认值
        if model_name is None:
            # 创建模型时传递默认值
            return model_class(**kwargs)
        else:
            # 使用传递的 model_name
            return model_class(model_name=model_name, **kwargs)


class LLM:
    def __init__(self, model_type, model_name = None, demo_path = "./models/language/demo.txt", compiler_path = "./models/language/RSLLang.jar", 
                 prompt_path = "./prompts/ifelseloop_prompt.json", shots_path = "./shots/framework_shots.json", memory = ''):
        self.model_type = model_type
        self.model_name = model_name
        self.demo_path = demo_path
        self.compiler_path = compiler_path
        self.prompt_path = prompt_path
        self.shots_path = shots_path
        self.memory = memory
        self.shots = self._load_shots()
        self.messages = self._load_system_message()
        self.pattern = r"```(?:\w*)(?:\s*)([^`]*)```"
        
        # Initialize Llama model
        self.llm = LLMFactory.create_llm(model_type=self.model_type, model_name=self.model_name)

    def _load_system_message(self):
        # Load and format system messages
        with open(self.prompt_path, 'r', encoding='utf-8') as file:
            message = json.load(file)
        prompt = "\n".join([message['system'], message['lexer'], message['parser']]) + "\n" + self.shots + "\n"

        system_message = [{"role": "system", "content": prompt}]
        return system_message

    def _load_shots(self):
        """
        Load prompt examples to ensure that the generated shots align with the desired format.
        """
        shots = ["Here are some reference examples. You can use these instances to generate code for a custom-designed robot control language:\n"]
        with open(self.shots_path, 'r', encoding='utf-8') as file:
            shot_items = json.load(file)
        for _, item in shot_items.items():
            for key, value in item.items():
                shots.append(f"{key}: {value.strip()}")
        return '\n'.join(shots)

    
    def add_message(self, role, content):
        """
        添加一条消息到会话中。
        """
        self.messages.append({"role": role, "content": content})


    def generate_code(self, task, newmomery = None, error = ''):
        # Generate code based on task and model settings
        # 只需要持续调用generate_code就行了，会自动记录之前的对话的，不提供newmomery就代表不用更新
        if newmomery == None:
            newmomery = self.memory

        self.add_message("user",newmomery + '\n' + task + " : \n" + error)
        print(self.messages)
        output = self.llm.create_chat_completion(messages=self.messages)
        self.add_message("assistant",output)
        print("LLM生成:\n" + output + "\n")
        
        # Extract code block from output
        matches = re.findall(self.pattern, output)
        if matches:
            code = matches[0]
        else:
            raise ValueError("LLM is unable to understand the code generation task and did not generate any code.")

        return code

    def save_output(self, local_path, stdout):
        # Save compilation output to file
        with open(local_path, 'w') as file:
            file.write(stdout)

# Example of how to use the LLM class
if __name__ == '__main__':
    llm = LLM(
        model_type="api",
    )
    task = "I'm thirsty!"
    local_path = "./output/result.txt"
    code = llm.generate_code(task)
    print(code)
    code = llm.generate_code(" based on the environtment info generate new code",'there is a cup in front of user! dont grasp bottle for user!')
    print(code)