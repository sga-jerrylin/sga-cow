Qwen3-ASR
录音文件URL
import os
import dashscope

messages = [
    {
        "role": "system",
        "content": [
            # 此处用于配置定制化识别的Context
            {"text": ""},
        ]
    },
    {
        "role": "user",
        "content": [
            {"audio": "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"},
        ]
    }
]
response = dashscope.MultiModalConversation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key = "sk-xxx"
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen3-asr-flash",
    messages=messages,
    result_format="message",
    asr_options={
        # "language": "zh", # 可选，若已知音频的语种，可通过该参数指定待识别语种，以提升识别准确率
        "enable_lid":True,
        "enable_itn":False
    }
)
print(response)



本地文件

使用DashScope SDK处理本地图像文件时，需要传入文件路径。请您参考下表，结合您的使用方式与操作系统进行文件路径的创建。

系统

SDK

传入的文件路径

示例

Linux或macOS系统

Python SDK

file://{文件的绝对路径}

file:///home/images/test.png

Java SDK

Windows系统

Python SDK

file://{文件的绝对路径}

file://D:/images/test.png

Java SDK

file:///{文件的绝对路径}

file:///D:images/test.png


import os
import dashscope

# 请用您的本地音频的绝对路径替换 ABSOLUTE_PATH/welcome.mp3
audio_file_path = "file://ABSOLUTE_PATH/welcome.mp3"

messages = [
    {
        "role": "system",
        "content": [
            # 此处用于配置定制化识别的Context
            {"text": ""},
        ]
    },
    {
        "role": "user",
        "content": [
            {"audio": audio_file_path},
        ]
    }
]
response = dashscope.MultiModalConversation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key = "sk-xxx",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen3-asr-flash",
    messages=messages,
    result_format="message",
    asr_options={
        # "language": "zh", # 可选，若已知音频的语种，可通过该参数指定待识别语种，以提升识别准确率
        "enable_lid":True,
        "enable_itn":False
    }
)
print(response)



流式输出


模型并不是一次性生成最终结果，而是逐步地生成中间结果，最终结果由中间结果拼接而成。使用非流式输出方式需要等待模型生成结束后再将生成的中间结果拼接后返回，而流式输出可以实时地将中间结果返回，您可以在模型进行输出的同时进行阅读，减少等待模型回复的时间。您可以根据调用方式来设置不同的参数以实现流式输出：

DashScope Python SDK方式：设置stream参数为true。

DashScope Java SDK方式：需要通过streamCall接口调用。

DashScope HTTP方式：需要在Header中指定X-DashScope-SSE为enable。

import os
import dashscope

messages = [
    {
        "role": "system",
        "content": [
            # 此处用于配置定制化识别的Context
            {"text": ""},
        ]
    },
    {
        "role": "user",
        "content": [
            {"audio": "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"},
        ]
    }
]
response = dashscope.MultiModalConversation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key = "sk-xxx"
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model="qwen3-asr-flash",
    messages=messages,
    result_format="message",
    asr_options={
        # "language": "zh", # 可选，若已知音频的语种，可通过该参数指定待识别语种，以提升识别准确率
        "enable_lid":True,
        "enable_itn":False
    },
    stream=True
)

for response in response:
    try:
        print(response["output"]["choices"][0]["message"].content[0]["text"])
    except:
        pass