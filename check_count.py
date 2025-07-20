import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def check_file_count(input_dir, output_dir):
    """检查输入和输出文件夹中的jpg文件数量是否一致，支持子文件夹"""
    
    # 统计输入文件夹中所有子文件夹的jpg文件
    input_count = 0
    input_subdirs = []
    for item in os.listdir(input_dir):
        item_path = os.path.join(input_dir, item)
        if os.path.isdir(item_path):
            input_subdirs.append(item)
            files = [f for f in os.listdir(item_path) if f.lower().endswith('.jpg')]
            input_count += len(files)
    
    # 统计输出文件夹中所有子文件夹的jpg文件
    output_count = 0
    output_subdirs = []
    for item in os.listdir(output_dir):
        item_path = os.path.join(output_dir, item)
        if os.path.isdir(item_path):
            output_subdirs.append(item)
            files = [f for f in os.listdir(item_path) if f.lower().endswith('.jpg')]
            output_count += len(files)
    
    logging.info(f"输入文件夹: {input_count} 张图片（来自 {len(input_subdirs)} 个子文件夹），输出文件夹: {output_count} 张图片（来自 {len(output_subdirs)} 个子文件夹）")
    
    if output_count == input_count:
        logging.info("文件数量校验通过，输出量等于输入量。")
        return True
    else:
        logging.error(f"文件数量不符，输入: {input_count}，输出: {output_count}，请检查！")
        return False

if __name__ == "__main__":
    # TODO: 填写参数
    check_file_count("input", "output") 