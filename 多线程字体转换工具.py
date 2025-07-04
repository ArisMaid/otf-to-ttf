#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多线程字体转换工具
功能：将指定目录中的所有OTF字体文件转换为TTF格式
特性：
1. 智能线程管理（自动CPU核心检测，动态线程控制）
2. 实时进度显示（百分比、成功/失败标记）
3. 详细错误处理和性能统计
4. 彩色终端输出
5. UTF-8编码支持
"""

import os
import sys
import time
import subprocess
import platform
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

# 彩色输出支持
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

# 操作系统检测
IS_WINDOWS = platform.system() == 'Windows'
TERMINAL_WIDTH = 80

def print_header(title):
    """打印彩色标题"""
    print(f"{Color.BOLD}{Color.CYAN}{'=' * TERMINAL_WIDTH}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}{title.center(TERMINAL_WIDTH)}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}{'=' * TERMINAL_WIDTH}{Color.RESET}\n")

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """显示进度条"""
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r{prefix} |{Color.GREEN}{bar}{Color.RESET}| {percent}% {suffix}')
    sys.stdout.flush()
    if iteration == total:
        print()

def get_otf_files(directory):
    """获取目录中的所有OTF文件"""
    return [os.path.join(directory, f) for f in os.listdir(directory) 
            if f.lower().endswith('.otf') and os.path.isfile(os.path.join(directory, f))]

def convert_otf_to_ttf(file_path):
    """转换单个OTF文件到TTF格式"""
    start_time = time.time()
    filename = os.path.basename(file_path)
    result = {"filename": filename, "success": False, "error": "", "time": 0}
    
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            result["error"] = "文件不存在"
            return result
            
        # 执行转换命令
        process = subprocess.run(
            ["otf2ttf", file_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # 检查转换结果
        if process.returncode == 0:
            result["success"] = True
        else:
            # 提取错误信息
            error_lines = process.stderr.strip().split('\n')
            result["error"] = error_lines[-1] if error_lines else "未知错误"
    except Exception as e:
        result["error"] = f"系统错误: {str(e)}"
    finally:
        result["time"] = time.time() - start_time
        return result

def main():
    # 设置UTF-8编码环境
    if IS_WINDOWS:
        os.system('chcp 65001 > nul')
    
    # 设置字体目录
    font_dir = r"D:\Software\PotPlayer\otf"
    
    # 获取OTF文件列表
    otf_files = get_otf_files(font_dir)
    total_files = len(otf_files)
    
    if total_files == 0:
        print(f"{Color.RED}错误: 在目录中未找到OTF文件{Color.RESET}")
        return
    
    # 智能线程管理
    cpu_cores = os.cpu_count() or 1
    max_threads = min(cpu_cores * 2, 32)  # 不超过32线程
    
    print_header(f"字体转换工具 - v1.0")
    print(f"{Color.BOLD}目录:{Color.RESET} {font_dir}")
    print(f"{Color.BOLD}文件:{Color.RESET} {total_files} 个OTF文件")
    print(f"{Color.BOLD}线程:{Color.RESET} {max_threads} (基于 {cpu_cores} CPU核心)")
    print(f"{Color.BOLD}开始时间:{Color.RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 性能统计
    start_total_time = time.time()
    success_count = 0
    failed_count = 0
    processed_count = 0
    total_processing_time = 0
    
    # 创建线程池
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # 提交所有转换任务
        future_to_file = {
            executor.submit(convert_otf_to_ttf, file): file 
            for file in otf_files
        }
        
        # 处理完成的任务
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            processed_count += 1
            
            try:
                result = future.result()
            except Exception as e:
                result = {
                    "filename": os.path.basename(file_path),
                    "success": False,
                    "error": f"任务异常: {str(e)}",
                    "time": 0
                }
            
            # 更新统计
            if result["success"]:
                success_count += 1
                status = f"{Color.GREEN}✓ 成功{Color.RESET}"
            else:
                failed_count += 1
                status = f"{Color.RED}× 失败{Color.RESET}"
            
            total_processing_time += result["time"]
            
            # 显示结果
            filename_display = result["filename"][:40] + (result["filename"][40:] and '..')
            time_display = f"{result['time']:.3f}s"
            
            # 进度显示
            progress_prefix = f"进度: {processed_count}/{total_files} "
            print_progress_bar(processed_count, total_files, prefix=progress_prefix)
            
            # 详细结果
            result_line = f"\r{progress_prefix} | {filename_display.ljust(42)} | {status} | {time_display}"
            if not result["success"]:
                result_line += f" | {Color.YELLOW}错误: {result['error'][:50]}{Color.RESET}"
            
            sys.stdout.write(result_line)
            sys.stdout.flush()
    
    # 性能统计
    end_total_time = time.time()
    total_duration = end_total_time - start_total_time
    avg_time_per_file = total_processing_time / total_files if total_files > 0 else 0
    files_per_second = success_count / total_duration if total_duration > 0 else 0
    
    # 打印最终报告
    print(f"\n\n{Color.BOLD}{'转换结果'.center(TERMINAL_WIDTH, '=')}{Color.RESET}")
    print(f"{Color.GREEN}✓ 成功: {success_count} 个文件{Color.RESET}")
    print(f"{Color.RED}× 失败: {failed_count} 个文件{Color.RESET}")
    print(f"{Color.CYAN}总耗时: {timedelta(seconds=int(total_duration))} (平均 {avg_time_per_file:.3f} 秒/文件){Color.RESET}")
    print(f"{Color.MAGENTA}处理速度: {files_per_second:.2f} 文件/秒{Color.RESET}")
    print(f"{Color.BOLD}结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Color.RESET}")
    
    # 失败文件列表
    if failed_count > 0:
        print(f"\n{Color.BOLD}{Color.YELLOW}失败文件列表:{Color.RESET}")
        for future in future_to_file:
            try:
                result = future.result()
                if not result["success"]:
                    print(f"  - {result['filename']}: {Color.RED}{result['error']}{Color.RESET}")
            except:
                pass
    
    print(f"\n{Color.BOLD}{'=' * TERMINAL_WIDTH}{Color.RESET}")

if __name__ == "__main__":
    main()