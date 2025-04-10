import sys
import os
import re
import time
import json
import subprocess
from llama_cpp import Llama
import paramiko

host = '192.168.1.11'
port = 22
username = 'jetson'
password = 'yahboom'
local_path = './result/result.py'
remote_path = 'lidar_test/src/my_laser/scripts/test.py'
setup_path = 'lidar_test/src/my_laser/scripts/setup.py'
log_path = 'lidar_test/src/my_laser/scripts/log.txt'
command = f'roslaunch my_laser test.launch'
choice = 0

def send_and_execute_file(host, port, username, password, local_path, remote_path, command):
    # 创建 SSH 客户端
    client = paramiko.SSHClient()
    # 自动添加策略，保存服务器的主机名和密钥信息
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 连接到远程服务器
    client.connect(host, port, username, password)

    # 使用 SFTP 会话传输文件
    sftp = client.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()

    # 加载bash
    # stdin, stdout, stderr = client.exec_command('source ~/.bashrc')
    # output = stdout.read().decode()
    # error_output = stderr.read().decode()
    # print(output)
    # print(error_output)
    
    #在远程服务器上执行 Python 脚本
    stdin, stdout, stderr = client.exec_command('bash -i -c "roslaunch my_laser laser_test.launch"', get_pty=True)

    combined_output = []
    error_output = []
    interrupted = False

    # 持续读取合并后的输出
    while not stdout.channel.exit_status_ready() and not interrupted:
        if stdout.channel.recv_ready():
            # 读取标准输出（已包含标准错误）
            output = stdout.channel.recv(4096).decode()
            combined_output.append(output)
            print("合并输出: ", output)

            # 按行拆分，提取错误信息
            for line in output.splitlines():
                if line.startswith("#####"):  # 识别错误标记
                    error_output.append(line)
                    print("检测到错误，关闭 SSH 通道以中断进程...")
                    stdout.channel.close()  # 关闭通道，直接中断进程
                    interrupted = True
                    break

    # 确保命令结束后，读取所有剩余输出
    if not interrupted:
        combined_output.append(stdout.read().decode())

    # 关闭连接
    client.close()

    # 返回合并后的输出和提取的错误输出
    return ''.join(combined_output), '\n'.join(error_output)

def compile_program(code_path, compiler_path, program):
    with open(code_path, 'w', encoding='utf-8') as file: 
        print(program, file=file)
    command = ['java', '-jar', compiler_path, code_path]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout, result.stderr

if __name__ == '__main__':
    # variables
    stdout = None
    stderr = None
    EnvironmentError = None
    # related file paths
    demo_path = r"./models/language/demo.txt"
    compiler_path = r"./models/language/RSLLang.jar"

    # regular expression match
    pattern = r"```(?:\w*)(?:\s*)([^`]*)```"
    
    # Setting system message
    system_message = []
    with open("./prompts/framework_prompt.json", 'r', encoding='utf-8') as file:
        message = json.load(file)
    system = message['system']
    lexer = message['lexer']
    parser = message['parser']
    system_message.append(system)
    system_message.append(lexer)
    system_message.append(parser)
    system_message = "\n".join(system_message)

    # Setting shots
    shots = []
    with open("./shots/framework_shots.json", 'r', encoding='utf-8') as file:
        shot_items = json.load(file)
    for _, item in shot_items.items():
            shots.append(item['task'])
            shots.append(item['program'])
    shots = '\n'.join(shots)

    # Setting task
    task = "I'm thirsty!"

    llm = Llama(model_path = "./models/llama/gemma-2-9b-it-Q6_K.gguf", n_ctx=4096, chat_format="chatml", n_gpu_layers=-1)
    output = llm.create_chat_completion(
            messages = [
                {   "role": "system", "content": system_message + "\n" + shots + "\n"},
                {   "role": "user", "content": task + " : \n"}
            ]
        )['choices'][0]['message']['content']

    print("LLM生成:\n" + output + "\n")


    output = re.findall(pattern, output)[0]
    stdout, stderr = compile_program(demo_path, compiler_path, output)

    print("编译器编译结果:\n" + stdout + "\n" + stderr)
    print("Process completed successfully.")

    with open(local_path, 'w') as file:
        file.write(stdout)
    
    #stdout,EnvironmentError = send_and_execute_file(host, port, username, password, local_path, remote_path, command)
    #print(stdout)
