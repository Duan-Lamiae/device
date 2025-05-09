# -*- coding: utf-8 -*-
import asyncio
from openai import AsyncOpenAI
import time
import base64
import re
import json
from PIL import Image, ImageEnhance, ImageOps
from paddleocr import PaddleOCR
import numpy as np

json_schema = {
    "type": "object",
    "properties": {
        "is_zhibo": {"type": "boolean"},
        "is_game": {"type": "boolean"}
    }
}

json_output_prompt = f"""
请按照以下json的schema来返回，不要返回其他内容：{json_schema}, 
每个参数的含义分别是：
is_zhibo是否是直播界面, 如果不是就给False
is_game是否是游戏界面, 如果不是就给False
返回格式是json格式
"""
APIKEY = "sk-nccJPTABkAnDCiEdFcEcB4033e224b8887Ad100fEf275e25"
BASEURL = "http://10.120.0.139:8000/v1"

class ImageProcessor:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=APIKEY, base_url=BASEURL)
        # 初始化 PaddleOCR，指定中文识别
        self.ocr = PaddleOCR(lang='ch')  # 'ch' 表示中文

    async def process_image(self, image_data: bytes, prompt: str = json_output_prompt):
        
        
        # 读取并编码图片
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        image_base64 = f"data:image/jpeg;base64,{image_base64}"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_base64}},
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        params = {
            "model": "Qwen/Qwen2-VL-7B-Instruct",
            "messages": messages,
        }
        
        try:
            start_time = time.time()
            result = await self.client.chat.completions.create(**params)
            end_time = time.time()
            
            content = result.choices[0].message.content
            print(f"处理时间: {end_time - start_time:.2f}秒")

            image_data = {
                "is_zhibo": False,
                "is_game": False
            }
            # 用正则找到```json```之间的内容
            match = re.search(r'```json\s*([\s\S]*)\s*```', content)
            if match:
                content = match.group(1).strip()
            else:
                content = content.strip()
                
            # 尝试解析 JSON 数据
            try:
                image_data = json.loads(content)
                # 验证并设置默认值
                image_data = {
                    "is_zhibo": image_data.get("is_zhibo", False),
                    "is_game": image_data.get("is_game", False)
                }
            except json.JSONDecodeError:
                print("返回的内容不是有效的 JSON 格式", content)
                image_data = {
                    "is_zhibo": False,
                    "is_game": False
                }
            except Exception as e:
                print(f"API 调用出错: {e}")
            print("Qwen2-VL 图像处理时间", time.time() - start_time)
            return image_data
        except Exception as e:
            print(f"API 调用出错: {e}")
            return "抱歉，处理请求时出现错误。"

    async def ocr_image(self, image_path: str):
        """
        使用 PaddleOCR 识别图像中的中文文本
        """
        try:
            # 打开图像文件
            image = Image.open(image_path)
            print(f"成功打开图像")
        except Exception as e:
            print(f"无法打开图像文件: {e}")
            return []

        # 图像反转（可选，视具体需求而定）
        try:
            image = ImageOps.invert(image)
            print("图像已反转")
        except Exception as e:
            print(f"图像反转失败: {e}")

        # 图像增强（例如增加对比度）
        try:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)  # 增加对比度，参数可以调整
            print("图像对比度已增强")
        except Exception as e:
            print(f"图像增强失败: {e}")
        
        width, height = image.size
        left = 0
        upper = height * 0.5
        right = int(width)
        lower = int(height)
        # 裁剪图像
        try:
            image = image.crop((left, upper, right, lower))
            print("图像已裁剪")
        except Exception as e:
            print(f"图像裁剪失败: {e}")

        # 显示裁剪后的图像（可选）
        image.show()    
        # 保存裁剪后的图像以供验证（可选）
        # 转换为 RGB 模式，确保图像有3个通道
        image = image.convert('RGB')

        # 将 PIL.Image 转换为 numpy.ndarray
        cropped_image_np = np.array(image)

        # 使用 PaddleOCR 识别图像中的文字，指定语言为中文
        try:
            result = self.ocr.ocr(cropped_image_np, rec=True, cls=True)
        except Exception as e:
            print("PaddleOCR 识别失败:")
            print(e)
            return []

        # 检查 result 是否为空
        if not result:
            print("未检测到任何文本。")
            return []
        else:
            texts = []
            for image_result in result:
                if isinstance(image_result, list):
                    for line in image_result:
                        if isinstance(line, list) and len(line) >= 2:
                            text_info = line[1]
                            if isinstance(text_info, tuple) and len(text_info) >= 1:
                                text = text_info[0]
                                texts.append(text)
                            else:
                                print(f"意外的文本信息结构: {text_info}")
                        else:
                            print(f"意外的行结构: {line}")
                else:
                    print(f"意外的 image_result 类型: {image_result}")
            
            # 对识别的内容进行正则匹配，只保留中文，非中文的移除掉
            texts = [re.sub(r'[^\u4e00-\u9fa5]', '', text) for text in texts]
            texts = [text for text in texts if text]
            print(f"####识别的文字: {texts}")
            return texts
        
    