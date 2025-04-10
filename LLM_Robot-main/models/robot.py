import paramiko
import select
import time

# 全局配置变量
HOST = '192.168.1.11'
PORT = 22
USERNAME = 'jetson'
PASSWORD = 'yahboom'
LOCAL_PATH = './result/result.py'
REMOTE_PATH = 'lidar_test/src/my_laser/scripts/test.py'
LOG_PATH = 'lidar_test/src/my_laser/scripts/log.txt'
STOP_SIGNAL_FILE = 'lidar_test/src/my_laser/scripts/stop_signal.txt'

class SSHClient:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None

    def connect(self):
        """连接到远程服务器"""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host, self.port, self.username, self.password)

    def disconnect(self):
        """关闭与远程服务器的连接"""
        if self.client:
            self.client.close()

    def transfer_file(self, local_path, remote_path):
        """上传文件到远程服务器"""
        sftp = self.client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()

    def execute_command(self, command, timeout=10):
        command = 'roscore'
        """在远程服务器上执行命令，等待一段时间后返回输出，并在超时后中断命令"""
        stdin, stdout, stderr = self.client.exec_command(f'bash -i -c "{command}"', get_pty=True)

        output = ""
        error = ""
        start_time = time.time()

        while time.time() - start_time < timeout:  # 等待指定时间
            if stdout.channel.recv_ready():  # 检查是否有输出可以读取
                rl, wl, xl = select.select([stdout.channel], [], [], 1.0)
                if rl:
                    line = stdout.channel.recv(1024).decode()  # 每次读取 1024 字节
                    output += line
                    print(line, end="")  # 如果需要可以实时打印输出

            # 检查标准错误输出
            if stderr.channel.recv_ready():
                error += stderr.read().decode()

            time.sleep(0.1)  # 避免 CPU 占用过高，稍微休眠一下

        # 超时后，尝试终止远程命令
        stdout.channel.send("\x03")  # 发送中断信号 (Ctrl+C)

        # 确保通道关闭
        stdout.channel.close()
        stderr.channel.close()
        
        return output, error


    def read_log(self, log_path):
        """读取远程日志文件并返回其内容"""
        stdin, stdout, stderr = self.client.exec_command(f'cat {log_path}')
        log_content = stdout.read().decode()
        return log_content
    
    def check_file_exists(self, file_path):
        """检查远程文件是否存在"""
        stdin, stdout, stderr = self.client.exec_command(f'ls {file_path}')
        result = stdout.read().decode()
        return file_path in result


class Robot:
    def __init__(self):
        pass
        #self.ssh_client = SSHClient(HOST, PORT, USERNAME, PASSWORD)

    def initialize(self):
        """初始化机器人（具体内容根据需求实现）"""
        pass
        #self.ssh_client.connect()
        
    def perceive(self):
        """初始感知环境"""
        return ''
    
    def shutdown(self):
        """关闭机器人（具体内容根据需求实现）"""
        pass
        #self.ssh_client.disconnect()

    def execute_code(self):
        """执行REMOTE_PATH的文件并返回输出和错误信息"""
        output, errors = self.ssh_client.execute_command('python lidar_test/src/my_laser/scripts/run_test.py')
        print("执行输出:", output)
        print("错误输出:", errors)

    def send_code(self,code):
        '''将输入的代码字符串写到LOCAL_PATH并传输到REMOTE_PATH'''
        with open(LOCAL_PATH, 'w') as file:
            file.write(code)

        self.ssh_client.transfer_file(LOCAL_PATH,REMOTE_PATH)

    def get_log(self):
        """读取日志内容"""
        log_content = self.ssh_client.read_log(LOG_PATH)
        print("日志内容:", log_content)

    def monitor_stop_signal(self, check_interval=5):
        """通过新的SSH连接持续监听远程是否发送中止信号"""
        monitor_client = SSHClient(HOST, PORT, USERNAME, PASSWORD)
        monitor_client.connect()

        try:
            while True:
                if monitor_client.check_file_exists(STOP_SIGNAL_FILE):
                    print("检测到中止信号，停止操作。")
                    break
                print("未检测到中止信号，继续监听...")
                time.sleep(check_interval)
        finally:
            monitor_client.disconnect()

# 示例用法
if __name__ == "__main__":
    robot = Robot()
    robot.initialize()  # 初始化机器人
    robot.send_code('hhhh')
    robot.execute_code()  # 执行远程命令
    robot.get_log()  # 获取日志
    robot.shutdown()  # 关闭连接
