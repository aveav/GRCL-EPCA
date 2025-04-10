from memory import *
from LLM import *
from compiler import *
from robot import *

MAX_ITERATION = 10
ERROR_PROMPT = "Please revise the code in the memory under 'Code Not Executed' as it contains the following errors:"
ENVIRONMENT_PROMPT = "Based on the above memory information, if necessary, modify the code under 'Code Not Executed' to ensure that the original user task is completed."
# Note that the memory information includes all available objects; please do not attempt to interact with any objects that are not present."

class MemoryManager:
    def __init__(self, simulation_mode=False, simulation_file=None):
        # Memory 仅由 MemoryManager 管理
        self.memory = Memory()
        self.simulation_mode = simulation_mode  # 是否处于模拟模式
        self.simulation_file = simulation_file  # 模拟模式使用的 JSON 文件
        self.simulation_data = []  # 用于存储从 JSON 文件中加载的数据
        self.simulation_index = 0  # 当前模拟数据的索引

        if self.simulation_mode and self.simulation_file:
            self._load_simulation_data()

    def _load_simulation_data(self):
        """
        从 JSON 文件中加载模拟数据。
        """
        with open(self.simulation_file, 'r') as file:
            self.simulation_data = json.load(file)

    def initialize_memory(self, initial_data):
        """
        使用机器人传递的初始数据来初始化 Memory
        :param initial_data: 初始数据
        """
        if self.simulation_mode:
            # 在模拟模式下，从模拟数据中加载初始 Memory
            self._apply_simulation_data()
        else:
            # 非模拟模式，使用实际数据初始化
            pass  # 根据需求填充初始化逻辑

    def update_memory_from_environment(self, raw_data):
        """
        接受未经处理的机器人环境数据，并根据需要更新 Memory。
        :param raw_data: 未处理的环境数据
        :return: 是否真的更改了 Memory，True 表示更改，False 表示未更改
        """
        if self.simulation_mode:
            # 在模拟模式下，从模拟数据中读取下一步的 Memory
            self._apply_simulation_data()
            return True
        else:
            # 非模拟模式，处理实际数据并更新 Memory
            pass

    def _apply_simulation_data(self):
        """
        应用当前模拟数据到 Memory。
        """
        if self.simulation_index < len(self.simulation_data):
            data = self.simulation_data[self.simulation_index]
            self.memory.objects = data.get('objects', {})
            self.memory.user_position = tuple(data.get('user_position', (0, 0)))
            self.memory.robot_position = tuple(data.get('robot_position', (0, 0)))
            self.memory.obstacles = set(tuple(obs) for obs in data.get('obstacles', []))
            self.simulation_index += 1
        else:
            raise RuntimeError('已经完成模拟了')

    def update_memory_from_compiler(self, stderr, executed_code, remaining_code):
        """
        根据编译器的返回结果更新 Memory。
        注意后面这里还有两个逻辑需要实现。
        一个是指令成功执行了，一个是环境发现指令无法执行。
        """
        if stderr:
            # 有错的话，没有任何代码被执行
            self.memory.update_code_not_executed(executed_code + '\n' + remaining_code)
        else:
            self.memory.add_executed_code(executed_code)
            self.memory.clear_code_not_executed()
            
            if remaining_code:  # 如果有未编译的代码，更新 code_not_executed
                self.memory.update_code_not_executed(remaining_code)

    def get_memory_summary(self):
        """
        输出 Memory 的摘要信息。
        :return: Memory 的摘要信息字符串
        """
        return MemorySummary.get_summary(self.memory)



class SystemController:
    def __init__(self, model,simulation_mode=False, simulation_file=None):
        # 初始化各个模块
        self.robot = Robot()
        self.simulation_mode = simulation_mode
        self.memory_manager = MemoryManager(simulation_mode, simulation_file)  # 使用 MemoryManager 管理 memory
        self.llm = LLM(
            model_type=model
        )
        self.compiler = Compiler(
            compiler_path="./models/language/RSLLang.jar",
            code_path="./models/language/demo.txt"
        )

    def initialize_system(self):
        """初始化系统和各模块"""
        self.robot.initialize()
        # 从机器人获取初始数据并初始化 memory
        initial_data = self.robot.perceive()
        self.memory_manager.initialize_memory(initial_data)
        print("系统初始化完成")

    def handle_task(self, task):
        """负责与编译器沟通，完成一次语法上没有错误的执行"""
        # 获取当前环境记忆的摘要
        memory_summary = self.memory_manager.get_memory_summary()
        # 生成代码
        generated_code = self.llm.generate_code(task, newmomery=memory_summary, error='')
        print("生成的代码:", generated_code)

        # 编译代码
        stdout, stderr = self.compiler.compile_code(generated_code)
        
        iteration_cnt = 0;
        while iteration_cnt < MAX_ITERATION and stderr:
            generated_code = self.llm.generate_code(ERROR_PROMPT, newmomery=memory_summary, error=stderr)
            print("生成的代码:", generated_code)

            stdout, stderr = self.compiler.compile_code(generated_code)

        # 如果编译成功，则执行代码
        if self.simulation_mode:
            stopped= True
            reason = "failed"
        else:
            self.robot.send_code(stdout)
            self.robot.execute_code()
            stopped, reason = self.robot.monitor_stop_signal()

        return stopped, reason

    
    def launch_system(self,user_task):
        """负责一直运行，直到机器人正常完成任务"""
        while True:
            stopped, reason = self.handle_task(user_task)

            if stopped and "succeed" in reason.lower():
                print("任务成功完成。")
                self.memory_manager.update_memory_from_environment(f"任务成功完成，原因: {reason}")
                break
            elif stopped and "failed" in reason.lower():
                print("任务失败，原因:", reason)
                self.memory_manager.update_memory_from_environment(f"任务失败，原因: {reason}")
                user_task = ENVIRONMENT_PROMPT
            elif stopped:
                print("任务中止，原因未知:", reason)
                break

    def shutdown_system(self):
        """关闭系统和所有连接"""
        self.robot.shutdown()
        print("系统已关闭")


# 示例用法
if __name__ == "__main__":
    simulation_file = "simulation\simulation_data.json"  # 模拟数据文件路径
    '''
    "llama": LlamaLLM,
    "ollama": OllamaLLM,
    "api":APILLM,
    '''
    controller = SystemController(model='api',simulation_mode=True, simulation_file=simulation_file)  # 启动模拟模式

    # 初始化系统
    controller.initialize_system()

    # 设置一个任务
    task = "I'm thirsty!"

    # 处理任务
    controller.launch_system(task)
