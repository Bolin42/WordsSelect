# -*- coding: utf-8 -*-
# 使用阿里云官方推荐的新版API批量图片识别
import dotenv
import os
import sys
import json
from typing import List
from alibabacloud_ocr_api20210707.client import Client as ocr_api20210707Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_darabonba_stream.client import Client as StreamClient
from alibabacloud_ocr_api20210707 import models as ocr_api_20210707_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

class AliyunOCRBatch:
    def __init__(self):
        self.client = self.create_client()

    @staticmethod
    def create_client() -> ocr_api20210707Client:
        """
        使用凭据初始化账号Client
        """
        credential = CredentialClient()
        config = open_api_models.Config(credential=credential)
        config.endpoint = 'ocr-api.cn-hangzhou.aliyuncs.com'
        return ocr_api20210707Client(config)

    def recognize_image(self, image_path: str) -> dict:
        """
        识别单张图片，返回结构化JSON
        """
        # 使用官方推荐的StreamClient读取文件
        body_stream = StreamClient.read_from_file_path(image_path)
        
        recognize_request = ocr_api_20210707_models.RecognizeAdvancedRequest(
            output_char_info=False,
            need_rotate=True,
            output_table=False,
            need_sort_page=True,
            output_figure=False,
            no_stamp=False,
            paragraph=True,
            row=True,
            body=body_stream
        )
        runtime = util_models.RuntimeOptions()
        try:
            response = self.client.recognize_advanced_with_options(recognize_request, runtime)
            # 返回body内容（结构化JSON）
            return response.body.to_map()
        except Exception as error:
            print(f"识别失败: {image_path}")
            print(f"错误信息: {str(error)}")
            return {}

    def batch_recognize(self, input_dir: str, output_dir: str, exts: List[str] = [".jpg", ".jpeg", ".png"]):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        subdirs = []
        for item in os.listdir(input_dir):
            item_path = os.path.join(input_dir, item)
            if os.path.isdir(item_path):
                subdirs.append(item)
        subdirs.sort()
        print(f"找到 {len(subdirs)} 个子文件夹，按正常顺序排序: {subdirs}")
        for subdir in subdirs:
            subdir_path = os.path.join(input_dir, subdir)
            files = [f for f in os.listdir(subdir_path) if os.path.splitext(f)[1].lower() in exts]
            if not files:
                continue
            subdir_output = os.path.join(output_dir, subdir)
            if not os.path.exists(subdir_output):
                os.makedirs(subdir_output)
            print(f"处理 {subdir} 文件夹, 共 {len(files)} 张图片")
            for fname in files:
                img_path = os.path.join(subdir_path, fname)
                out_path = os.path.join(subdir_output, os.path.splitext(fname)[0] + ".json")
                print(f"识别: {subdir}/{fname}")
                result = self.recognize_image(img_path)
                if result:
                    with open(out_path, 'w', encoding='utf-8') as f:
                        f.write(json.dumps(result, ensure_ascii=False, indent=2))
                    print(f"输出: {out_path}")
                else:
                    print(f"识别失败: {subdir}/{fname}")

def ocr_alicloud_batch(input_dir: str, output_dir: str):
    """兼容旧接口的函数"""
    ocr = AliyunOCRBatch()
    ocr.batch_recognize(input_dir, output_dir)

if __name__ == '__main__':
    # 用法: python ocr_alicloud.py input_dir output_dir
    if len(sys.argv) != 3:
        print("用法: python ocr_alicloud.py <图片目录> <输出目录>")
        sys.exit(1)
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    ocr = AliyunOCRBatch()
    ocr.batch_recognize(input_dir, output_dir) 