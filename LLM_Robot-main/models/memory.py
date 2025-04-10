class Memory:
    def __init__(self):
        # 初始化物体、已执行代码、未执行代码的存储以及被移除物体的集合
        self.objects = {}  # 存储识别到的物体名称及其坐标，格式为 {'object_name': (x, y)}
        self.executed_code = []  # 存储已执行的代码列表
        self.code_not_executed = ""  # 存储未执行的代码（单字符串）
        self.removed_objects = set()  # 存储被移除的物体名称集合
        self.user_position = (0, 0)  # 记录用户当前的坐标，初始化为(0, 0)
        self.robot_position = (0, 0)  # 记录机器人当前的坐标，初始化为(0, 0)
        self.obstacles = set()  # 存储障碍物坐标，格式为 {(x, y)}

    def add_object(self, name, position):
        """
        添加或更新物体信息。如果该物体在被移除集合中，则将其从集合中移除。
        :param name: 物体名称
        :param position: 物体坐标，格式为(x, y)
        """
        if name in self.removed_objects:
            self.removed_objects.remove(name)  # 从被移除集合中恢复
        self.objects[name] = position

    def remove_object(self, name):
        """
        移除特定的物体，并将该物体记录到被移除集合中。
        :param name: 物体名称
        """
        if name in self.objects:
            del self.objects[name]
            self.removed_objects.add(name)  # 记录到被移除集合中

    def add_executed_code(self, code):
        """
        添加已执行代码。
        :param code: 已执行的代码内容
        """
        self.executed_code.append(code)

    def update_code_not_executed(self, code):
        """
        更新未执行的代码（覆盖更新）。
        :param code: 新的未执行的代码内容
        """
        self.code_not_executed = code

    def clear_code_not_executed(self):
        """清空未执行的代码。"""
        self.code_not_executed = ""

    def update_user_position(self, position):
        """
        更新用户当前坐标。
        :param position: 用户坐标，格式为(x, y)
        """
        self.user_position = position

    def update_robot_position(self, position):
        """
        更新机器人当前坐标。
        :param position: 机器人坐标，格式为(x, y)
        """
        self.robot_position = position

    def add_obstacle(self, position):
        """
        添加障碍物坐标。
        :param position: 障碍物坐标，格式为(x, y)
        """
        self.obstacles.add(position)

    def remove_obstacle(self, position):
        """
        移除障碍物坐标。
        :param position: 障碍物坐标，格式为(x, y)
        """
        self.obstacles.discard(position)

    def reset_memory(self):
        """重置所有记忆信息。"""
        self.objects.clear()
        self.executed_code.clear()
        self.code_not_executed = ""
        self.removed_objects.clear()
        self.user_position = (0, 0)
        self.robot_position = (0, 0)
        self.obstacles.clear()


class MemorySummary:
    @staticmethod
    def get_summary(memory):
        """
        获取当前记忆的总结信息，便于反馈给大模型。
        :param memory: Memory类的实例
        :return: 总结字符串
        """
        summary = "Memory Information:\n"
        summary += "Objects:\n"
        for name, position in memory.objects.items():
            summary += f"  - {name} at {position}\n"

        summary += "These objects can no longer be found. Do not attempt to perform any operations on them:\n"
        for name in memory.removed_objects:
            summary += f"  - {name}\n"

        summary += "Executed Code:\n"
        for i, code in enumerate(memory.executed_code, 1):
            summary += f"  {i}. {code}\n"

        summary += "Code Not Executed:\n"
        summary += f"  {memory.code_not_executed}\n" if memory.code_not_executed else "  None\n"

        summary += f"User Position: {memory.user_position}\n"
        summary += f"Robot Position: {memory.robot_position}\n"

        summary += "Obstacles:\n"
        for position in memory.obstacles:
            summary += f"  - {position}\n"

        return summary

    @staticmethod
    def get_summary_for_basic_llm(memory):
        """
        获取当前记忆的总结信息，便于反馈给基础大模型。
        :param memory: Memory类的实例
        :return: 总结字符串
        """
        pass