import re
import json
import subprocess
from llama_cpp import Llama

def compile_program(demo_path, compiler_path, interface_path, program):
    with open(demo_path, 'w', encoding='utf-8') as file: 
        print(program, file=file)
    command = ['java', '-jar', compiler_path, demo_path, interface_path]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout, result.stderr

if __name__ == '__main__':
    
    # variables
    stdout = None
    stderr = None

    # related file paths
    demo_path = r"./models/language/demo.txt"
    interface_path = r"./models/language/interface.txt"
    compiler_path = r"./models/language/RCLLang.jar"

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
    task = input("Typing your task: ")

    # Models Llama-3.1-8B-it-Q6_K gemma-2-9b-it-Q6_K gemma-2-2b-it-Q6_K
    llm = Llama(model_path = "./models/llama/gemma-2-9b-it-Q6_K.gguf", n_ctx=4096, chat_format="chatml", n_gpu_layers=-1)

    for i in range(5):
        if stdout and (stderr == ''):
            break

        elif (stderr == '') or (stderr is None):
            output = llm.create_chat_completion(
                messages = [
                    {   "role": "system", "content": system_message + "\n" + shots + "\n"},
                    {   "role": "user", "content": task + " : \n"}
                ]
            )['choices'][0]['message']['content']

        else:
            output = llm.create_chat_completion(
                messages = [
                    {   "role": "system", "content": system_message + "\n" + shots + "\n"},
                    {   "role": "user", "content": task + "(fixing and avoiding the compiler errors: " + stderr.splitlines()[0] + ") : \n"}
                ]
            )['choices'][0]['message']['content']
            print(output, "\n")

        output = re.findall(pattern, output)[0]
        stdout, stderr = compile_program(demo_path, compiler_path, interface_path, output)
        
    print(output, "\n", stdout, "\n", stderr)
    print("Process completed successfully.")
