import os
from PIL import Image
from tqdm import tqdm
import logging
# 移除cv2和np依赖
import numpy as np
import cv2
import subprocess
import platform

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def open_image_file(file_path):
    """根据操作系统自动打开图片文件"""
    try:
        if platform.system() == "Darwin":       # macOS
            subprocess.call(('open', file_path))
        elif platform.system() == "Windows":    # Windows
            os.startfile(file_path)
        else:                                   # Linux
            subprocess.call(('xdg-open', file_path))
        return True
    except Exception as e:
        logging.warning(f"无法自动打开文件 {file_path}: {e}")
        return False

def ask_page_type_for_folder(folder_name, sample_file_path):
    """询问用户指定文件夹的页面类型"""
    print(f"\n📁 处理文件夹: {folder_name}")
    print(f"📄 自动打开示例文件: {os.path.basename(sample_file_path)}")
    
    # 自动打开示例文件
    if open_image_file(sample_file_path):
        print("✅ 已自动打开示例文件，请查看后选择页面类型")
    else:
        print("⚠️ 无法自动打开文件，请手动查看")
    
    while True:
        page_type = input(f"请选择 {folder_name} 文件夹的页面类型 (输入 'odd' 表示奇数页，'even' 表示偶数页): ").strip().lower()
        if page_type in ['odd', 'even']:
            return page_type
        else:
            print("❌ 输入无效，请输入 'odd' 或 'even'")

def detect_vertical_line(img, tolerance=10, min_ratio=0.95):
    """
    直接分析像素，找到允许左右偏差小于tolerance像素的最长竖直直线，返回中心x坐标。
    min_ratio: 连续像素占图片高度的最小比例
    """
    gray = img.convert('L')
    w, h = gray.size
    pixels = gray.load()
    threshold = 200  # 亮度阈值，低于此视为“黑线”
    max_len = 0
    best_x = None
    best_range = None
    for x in range(w):
        y = 0
        while y < h:
            # 跳过非黑色像素
            while y < h and pixels[x, y] > threshold:
                y += 1
            start_y = y
            # 统计连续黑色像素段
            while y < h and pixels[x, y] <= threshold:
                y += 1
            seg_len = y - start_y
            if seg_len > max_len:
                # 检查该段在x±tolerance范围内是否有其他列也有类似长度
                support = 0
                for dx in range(-tolerance, tolerance+1):
                    xx = x + dx
                    if 0 <= xx < w:
                        # 统计xx列的同区间黑色像素数
                        cnt = 0
                        for yy in range(start_y, y):
                            if pixels[xx, yy] <= threshold:
                                cnt += 1
                        if cnt >= seg_len * min_ratio:
                            support += 1
                if support >= tolerance:  # 至少有一半列支持
                    max_len = seg_len
                    best_x = x
                    best_range = (start_y, y)
            # 跳到下一个区段
            y += 1
    if best_x is not None:
        # 以支持区间的x中心为基准
        x_candidates = [xx for xx in range(best_x-tolerance, best_x+tolerance+1) if 0<=xx<w]
        center_x = int(sum(x_candidates)/len(x_candidates))
        return center_x
    return None

def process_images(input_dir, output_dir, y1, y2, x1, x2, first_page_type='odd'):
    """
    批量处理图片，按规则裁剪和拼接，输出到output_dir
    支持子文件夹处理，按文件夹名称逆序排序
    对每个文件夹单独询问页面类型
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 获取所有子文件夹，按逆序排序
    subdirs = []
    for item in os.listdir(input_dir):
        item_path = os.path.join(input_dir, item)
        if os.path.isdir(item_path):
            subdirs.append(item)
    
    subdirs.sort(reverse=True)  # 逆序排序
    logging.info(f"找到 {len(subdirs)} 个子文件夹，按逆序排序: {subdirs}")
    
    # 为每个文件夹确定页面类型
    folder_page_types = {}
    for subdir in subdirs:
        subdir_path = os.path.join(input_dir, subdir)
        files = [f for f in os.listdir(subdir_path) if f.lower().endswith('.jpg')]
        if files:
            # 获取第一个文件（逆序排序后的第一个）
            sample_file = files[0]
            sample_file_path = os.path.join(subdir_path, sample_file)
            page_type = ask_page_type_for_folder(subdir, sample_file_path)
            folder_page_types[subdir] = page_type
            print(f"✅ {subdir} 文件夹设置为: {page_type} 页面")
    
    # 统计总文件数
    total_files = 0
    for subdir in subdirs:
        subdir_path = os.path.join(input_dir, subdir)
        files = [f for f in os.listdir(subdir_path) if f.lower().endswith('.jpg')]
        total_files += len(files)
    
    logging.info(f"共检测到 {total_files} 个jpg文件，开始处理...")
    
    # 按文件夹分组处理文件
    for subdir in subdirs:
        subdir_path = os.path.join(input_dir, subdir)
        files = [f for f in os.listdir(subdir_path) if f.lower().endswith('.jpg')]
        
        if not files:
            continue
            
        logging.info(f"处理文件夹 {subdir}，包含 {len(files)} 个文件")
        
        # 为当前文件夹创建输出目录
        subdir_output_path = os.path.join(output_dir, subdir)
        if not os.path.exists(subdir_output_path):
            os.makedirs(subdir_output_path)
        
        # 处理当前文件夹中的所有文件
        for idx, filename in enumerate(tqdm(files, desc=f"处理 {subdir} 文件夹")):
            img_path = os.path.join(subdir_path, filename)
            img_pil = Image.open(img_path)
            width, height = img_pil.size
            
            # 使用该文件夹的页面类型
            first_page_type = folder_page_types[subdir]
            
            # 基准判断：odd为右侧偏移x1，even为左侧偏移x1
            if first_page_type == 'odd':
                # 右为基准，删去右侧 x1 像素
                img_pil = img_pil.crop((0, 0, width - x1, height))
            else:
                # 左为基准，删去左侧 x1 像素
                img_pil = img_pil.crop((x1, 0, width, height))
            
            # y1/y2裁剪
            width, height = img_pil.size
            img_pil = img_pil.crop((0, y1, width, height - y2))
            
            # 转为cv2格式进行边缘检测
            img = np.array(img_pil.convert('RGB'))
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Sobel边缘检测（竖直方向）
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            abs_sobelx = np.absolute(sobelx)
            sobel_8u = np.uint8(abs_sobelx)
            
            # 二值化
            thresh = np.where(sobel_8u > 50, 255, 0).astype(np.uint8)
            
            # 垂直投影找到竖直直线
            vertical_projection = np.sum(thresh, axis=0)
            split_line = int(np.argmax(vertical_projection))
            
            # 以竖直直线为基准裁剪为左右两份
            width, height = img_pil.size
            left_img = img_pil.crop((0, 0, split_line, height))
            right_img = img_pil.crop((split_line, 0, width, height))
            
            # 上下拼接：左侧图像在上方，右侧图像在下方
            merged_height = left_img.height + right_img.height
            merged_width = max(left_img.width, right_img.width)
            merged_img = Image.new('RGB', (merged_width, merged_height))
            
            # 将左侧图像放在上方
            merged_img.paste(left_img, (0, 0))
            # 将右侧图像放在下方
            merged_img.paste(right_img, (0, left_img.height))
            
            # 保存拼接后的图片到对应首字母文件夹
            merged_name = f"{idx+1}_merged.JPG"
            merged_img.save(os.path.join(subdir_output_path, merged_name))
            logging.info(f"✅ 处理 {subdir}/{filename}，页面类型: {first_page_type}，自动识别分割线在 x={split_line} 处，已保存到 {subdir}/{merged_name}")
    
    logging.info("图片处理全部完成。")

if __name__ == "__main__":
    # TODO: 填写参数
    process_images("input", "output", y1=0, y2=0, x1=0, x2=0, first_page_type='odd') 