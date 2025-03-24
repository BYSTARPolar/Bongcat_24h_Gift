import cv2
import numpy as np
import pyautogui
import time
import mss
from PIL import Image
import logging
import os

# 配置日志记录
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def save_screenshot(screenshot, save_dir="screenshots"):
    """保存截图到指定目录"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)  # 如果目录不存在，则创建
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(save_dir, f"screenshot_{timestamp}.png")
    screenshot.save(save_path)
    logging.info(f"截图已保存: {save_path}")

def find_gift_on_screen(template_path, save_screenshots=False):
    """在整个屏幕中查找礼物图片，并返回其屏幕坐标"""
    try:
        # 使用mss截图（支持多显示器）
        with mss.mss() as sct:
            # 获取所有显示器的区域
            monitor_regions = sct.monitors[1:]  # 第一个monitor是所有显示器的总和，跳过它
            for i, monitor in enumerate(monitor_regions):
                screenshot = sct.grab(monitor)
                screenshot = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

                # 保存截图（如果需要）
                if save_screenshots:
                    save_screenshot(screenshot)

                # 将截图转换为OpenCV格式
                screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                # 加载礼物模板图片
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if template is None:
                    logging.error(f"无法加载模板图片: {template_path}")
                    return None

                # 模板匹配
                result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                # 设置匹配阈值
                threshold = 0.8
                if max_val >= threshold:
                    # 计算礼物中心位置（相对于当前显示器）
                    gift_width, gift_height = template.shape[1], template.shape[0]
                    center_x = monitor["left"] + max_loc[0] + gift_width // 2
                    center_y = monitor["top"] + max_loc[1] + gift_height // 2
                    logging.info(f"在显示器 {i + 1} 上找到礼物，位置: ({center_x}, {center_y})")
                    return center_x, center_y

        logging.info("未找到礼物")
        return None

    except Exception as e:
        logging.error(f"查找礼物时发生错误: {e}")
        return None

def click_until_gift_disappears(template_path, gift_location, click_interval=0.5):
    """持续点击礼物位置，直到礼物消失"""
    try:
        while True:
            # 点击礼物位置
            pyautogui.click(gift_location[0], gift_location[1])
            logging.info(f"点击礼物位置: ({gift_location[0]}, {gift_location[1]})")

            # 等待一段时间后重新检测
            time.sleep(click_interval)

            # 重新检测礼物是否存在
            if not find_gift_on_screen(template_path):
                logging.info("礼物已消失，停止点击")
                break

    except Exception as e:
        logging.error(f"持续点击时发生错误: {e}")

def main():
    template_path = './gift.png'  # 礼物模板图片路径
    check_interval = 600  # 检测间隔时间（秒）
    save_screenshots = False  # 是否保存截图
    click_interval = 0.5  # 持续点击的时间间隔（秒）

    while True:
        try:
            # 查找礼物
            gift_location = find_gift_on_screen(template_path, save_screenshots)
            if gift_location:
                # 持续点击直到礼物消失
                click_until_gift_disappears(template_path, gift_location, click_interval)
            time.sleep(check_interval)  # 每30秒检测一次
        except KeyboardInterrupt:
            logging.info("程序已手动停止")
            break
        except Exception as e:
            logging.error(f"主循环发生错误: {e}")
            time.sleep(check_interval)  # 发生错误后等待一段时间再继续

if __name__ == "__main__":
    main()