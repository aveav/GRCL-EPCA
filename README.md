# GRCL - EPCA 项目文档

## 一、项目概述

The open-source project "Intelligent Control for the Future" focuses on building a large language model (LLM)-based intelligent framework for translating natural language into robot action planning, known as GRCL - EPCA. The project aims to design a Robot Skill Language (RSL) that transforms natural language instructions into verifiable, structured intermediate representations, which are then compiled into executable robot code.  
Innovatively, the project introduces RSL as a linguistic bridge and integrates syntactic/semantic validation, formal verification, and feedback-based refinement mechanisms to significantly enhance the accuracy and robustness of the generated programs.  
In the MIT benchmark for robot instruction following, the framework achieved a 92.6% parsing accuracy, and improved the task success rate in unseen scenarios to 79.8%.

## 二、项目结构与核心模块

### 结构

GRCL-EPCA/
├── LLM_Robot-main/
│   ├── models/
│   │   ├── language/
│   │   │   └── demo.txt
│   │   └── ...
│   ├── simulation/
│   │   └── simulation_data.json
│   ├── shots/
│   │   └── framework_shots.json
│   └── ...
├── RSL_compiler-main/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/
│   │   │   │   └── org/
│   │   │   │       └── main/
│   │   │   │           ├── IR.java
│   │   │   │           ├── Parser.java
│   │   │   │           └── SemanticsHandler.java
│   │   │   └── resources/
│   │   │       └── input/
│   │   │           ├── TargetCode.json
│   │   │           └── input.txt
│   ├── .idea/
│   │   ├── encodings.xml
│   │   ├── misc.xml
│   │   ├── uiDesigner.xml
│   │   └── vcs.xml
│   ├── .gitignore
│   └── pom.xml
└── README.md


### （一）LLM_Robot 模块

此模块主要负责与大语言模型交互、控制机器人以及管理内存信息。

1. **LLM 类**（`GRCL - EPCA/LLM_Robot/main/models/LLM.py`）
    - 功能：调用大语言模型生成代码。
    - 主要方法：
        - `__init__`：初始化模型，加载系统提示信息和示例代码。
        - `generate_code`：根据任务和内存信息生成代码。
        - `add_message`：添加消息到会话中。
        - `save_output`：保存编译输出到文件。

2. **Robot 类**（位于 robot.py 和 test.py）
    - 功能：控制机器人的初始化、感知、代码执行、日志读取和中止信号监听等操作。
    - 主要方法：
        - `__init__`：初始化 SSH 客户端。
        - `initialize`：初始化机器人，连接到远程服务器。
        - `perceive`：初始感知环境。
        - `shutdown`：关闭机器人，断开与远程服务器的连接。
        - `execute_code`：执行远程代码并返回输出和错误信息。
        - `send_code`：将代码发送到远程服务器。
        - `get_log`：读取远程日志文件。
        - `monitor_stop_signal`：监听远程中止信号。

3. **MemoryManager 类**（framework.py）
    - 功能：管理机器人的内存信息，包括环境数据和代码执行情况。
    - 主要方法：
        - `__init__`：初始化内存管理器，加载模拟数据（如果处于模拟模式）。
        - `initialize_memory`：使用初始数据初始化内存。
        - `update_memory_from_environment`：根据环境数据更新内存。
        - `update_memory_from_compiler`：根据编译器结果更新内存。
        - `get_memory_summary`：输出内存的摘要信息。

4. **SystemController 类**（framework.py）
    - 功能：协调系统各模块，处理用户任务，直到任务完成或中止。
    - 主要方法：
        - `__init__`：初始化系统控制器，包括机器人、内存管理器、LLM 和编译器。
        - `initialize_system`：初始化系统和各模块。
        - `handle_task`：处理用户任务，生成代码、编译代码并执行。
        - `launch_system`：启动系统，持续处理任务直到任务完成。
        - `shutdown_system`：关闭系统和所有连接。

### （二）RSL_compiler 模块

该模块主要负责代码的编译工作，将生成的代码转换为可执行的 Python 代码。

1. **Parser 类**（Java 实现）
    - 功能：解析输入代码，生成语法分析树。
    - 主要方法：
        - `printAST`：打印解析后的语法分析树。
        - `handle_assignstatement_bymatch`：处理赋值语句的错误。
        - `skipSemi`：跳过分号，继续分析代码。
        - `printProductions`：打印所有的产生式规则。
        - `printPredictiveParsingTable`：打印预测分析表。
        - `buildPredictiveParsingTable`：构建预测分析表。
        - `eliminateDirectLeftRecursion`：消除直接左递归。
        - `printFirstSets`：打印所有的 first 集合。

2. **SemanticActions 类**
    - 功能：处理语义分析和代码生成。
    - 主要方法：
        - `visit_forwardCommand`：处理 `forward` 命令，生成相应的 Python 代码。
        - `visit_forStatement`：处理 `for` 循环语句，生成 Python 循环代码。
        - `visit_slamCommand`：处理 `slam` 命令，生成相应的 Python 代码。
        - `visit_mathExp`：处理数学表达式，生成相应的字符串表示。
        - `applyCodeFromConfig`：从配置文件中读取代码并应用到节点。
        - `visit_assignstatement`：处理赋值语句，包括变量注册和 CFG 节点添加。
        - `visit_condstatement`：处理分支语句，生成相应的 Python 代码。

3. **SemanticsHandler 类**
    - 功能：处理语义错误和输出生成的代码。
    - 主要方法：
        - `getSymbol`：获取符号信息。
        - `printGeneratedCode`：输出或处理生成的代码。

## 三、使用示例

以下是一个使用示例，展示如何使用 `SystemController` 类处理用户任务：

{
from models.framework import SystemController
simulation_file = "simulation/simulation_data.json"
controller = SystemController(model='api', simulation_mode=True, simulation_file=simulation_file)
controller.initialize_system()
task = "I'm thirsty!"
controller.launch_system(task)
controller.shutdown_system()
}
## 四、总结
The GRCL - EPCA project effectively enhances the accuracy and robustness of natural language to robot action planning by introducing the RSL language and various verification mechanisms. The project has a clear structure, with each module having a well-defined division of labor. The SystemController class can conveniently coordinate all modules to complete user tasks. During the usage process, attention should be paid to issues such as the simulation mode and remote server configuration to ensure the normal operation of the system.

## Citation
@misc{GRCL - EPCA,
  title = {GRCL - EPCA: A Natural Language to Robot Action Planning Intelligent Framework Based on LLM},
  author = {}, 
  howpublished = {}, 
  year = { },
  note = { }
}


