#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XServer GAME 自动登录主控脚本
联动 login.py 和 code.py 实现完全自动化的登录流程
"""

import os
import sys
import time
import subprocess
import threading
import queue
from pathlib import Path

# 导入自定义脚本模块
from login import XServerAutoLogin
from code import WebmailAutoLogin

# =====================================================================
#                          配置区域
# =====================================================================

# XServer登录信息配置
XSERVER_EMAIL = os.getenv("XSERVER_EMAIL", "faiz555@zmkk.edu.kg")
XSERVER_PASSWORD = os.getenv("XSERVER_PASSWORD", "faiz555!!")

# 邮箱验证码获取配置
WEBMAIL_URL = "https://zmkk.edu.kg/login"
WEBMAIL_USERNAME = os.getenv("WEBMAIL_USERNAME", "kaixa913")
WEBMAIL_PASSWORD = os.getenv("WEBMAIL_PASSWORD", "kaixa913!!")

# 流程控制配置
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
USE_HEADLESS = IS_GITHUB_ACTIONS or os.getenv("USE_HEADLESS", "false").lower() == "true"
VERIFICATION_TIMEOUT = 180  # 验证码获取超时时间（秒）

# =====================================================================
#                        主控制器类
# =====================================================================

class XServerMainController:
    """XServer GAME 自动登录主控制器"""
    
    def __init__(self):
        """初始化主控制器"""
        self.xserver_login = None
        self.webmail_login = None
        self.verification_code = None
        self.verification_queue = queue.Queue()
        self.login_state = "initial"  # initial, waiting_verification, completed, failed
        
    def create_xserver_login(self):
        """创建XServer登录实例"""
        try:
            # 临时修改login.py中的配置以支持外部控制
            self.xserver_login = XServerAutoLogin()
            self.xserver_login.email = XSERVER_EMAIL
            self.xserver_login.password = XSERVER_PASSWORD
            self.xserver_login.headless = USE_HEADLESS
            print("✅ XServer登录器初始化成功")
            return True
        except Exception as e:
            print(f"❌ XServer登录器初始化失败: {e}")
            return False
    
    def create_webmail_login(self):
        """创建邮箱登录实例"""
        try:
            self.webmail_login = WebmailAutoLogin()
            self.webmail_login.webmail_url = WEBMAIL_URL
            self.webmail_login.email = WEBMAIL_USERNAME
            self.webmail_login.password = WEBMAIL_PASSWORD
            self.webmail_login.headless = USE_HEADLESS
            print("✅ 邮箱登录器初始化成功")
            return True
        except Exception as e:
            print(f"❌ 邮箱登录器初始化失败: {e}")
            return False
    
    def start_xserver_login(self):
        """启动XServer登录流程"""
        try:
            print("🚀 开始XServer登录流程...")
            
            # 验证配置
            if not self.xserver_login.validate_config():
                return False
            
            # 设置驱动
            if not self.xserver_login.setup_driver():
                return False
            
            # 导航到登录页面
            if not self.xserver_login.navigate_to_login():
                return False
            
            # 执行登录操作
            if not self.xserver_login.perform_login():
                return False
            
            # 检查是否需要验证
            verification_result = self.xserver_login.handle_verification_page()
            if verification_result == "need_verification_code":
                print("🔐 检测到需要验证码，准备自动获取...")
                self.login_state = "waiting_verification"
                return "need_verification"
            elif verification_result == True:
                print("✅ 验证流程已完成")
                # 检查登录结果
                if self.xserver_login.handle_login_result():
                    self.login_state = "completed"
                    return True
                else:
                    self.login_state = "failed"
                    return False
            else:
                # 直接检查登录结果
                if self.xserver_login.handle_login_result():
                    self.login_state = "completed"
                    return True
                else:
                    self.login_state = "failed"
                    return False
                    
        except Exception as e:
            print(f"❌ XServer登录流程失败: {e}")
            self.login_state = "failed"
            return False
    
    def get_verification_code_async(self):
        """异步获取验证码"""
        def get_code():
            try:
                print("📧 开始获取邮箱验证码...")
                
                # 等待一段时间让验证码邮件发送
                print("⏰ 等待验证码邮件发送...")
                time.sleep(30)
                
                # 初始化并运行邮箱登录
                if not self.webmail_login.setup_driver():
                    self.verification_queue.put(None)
                    return
                
                if not self.webmail_login.navigate_to_webmail():
                    self.verification_queue.put(None)
                    return
                
                if not self.webmail_login.perform_login():
                    self.verification_queue.put(None)
                    return
                
                if not self.webmail_login.check_login_result():
                    self.verification_queue.put(None)
                    return
                
                if not self.webmail_login.select_target_mailbox():
                    self.verification_queue.put(None)
                    return
                
                # 搜索验证邮件并提取验证码
                if self.webmail_login.search_verification_email():
                    code = self.webmail_login.extract_verification_code()
                    self.verification_queue.put(code)
                else:
                    self.verification_queue.put(None)
                    
            except Exception as e:
                print(f"❌ 获取验证码过程出错: {e}")
                self.verification_queue.put(None)
            # 注意：不在这里清理浏览器，等验证码输入完成后再清理
        
        # 在新线程中启动验证码获取
        thread = threading.Thread(target=get_code)
        thread.daemon = True
        thread.start()
        return thread
    
    def wait_for_verification_code(self, timeout=VERIFICATION_TIMEOUT):
        """等待验证码获取完成"""
        try:
            print(f"⏰ 等待验证码获取完成 (超时: {timeout}秒)...")
            
            # 启动异步获取验证码
            code_thread = self.get_verification_code_async()
            
            # 等待结果
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # 检查是否有验证码结果
                    code = self.verification_queue.get(timeout=5)
                    if code:
                        print(f"✅ 成功获取验证码: {code}")
                        self.verification_code = code
                        return code
                    else:
                        print("❌ 验证码获取失败")
                        return None
                except queue.Empty:
                    # 继续等待
                    print("⏳ 继续等待验证码...")
                    continue
            
            print("⏰ 验证码获取超时")
            return None
            
        except Exception as e:
            print(f"❌ 等待验证码时出错: {e}")
            return None
    
    def input_verification_code(self, code):
        """向XServer页面输入验证码"""
        try:
            print(f"🔑 将验证码输入到XServer页面: {code}")
            
            # 使用login.py的外部验证码输入方法
            return self.xserver_login.input_verification_code_externally(code)
            
        except Exception as e:
            print(f"❌ 输入验证码失败: {e}")
            return False
    
    def complete_login_flow(self):
        """完成登录流程"""
        try:
            print("🔍 正在检查最终登录结果...")
            
            # 检查登录结果
            if self.xserver_login.handle_login_result():
                print("🎉 XServer GAME 自动登录流程完成！")
                self.xserver_login.take_screenshot("login_completed")
                self.login_state = "completed"
                return True
            else:
                print("❌ 最终登录验证失败")
                self.login_state = "failed"
                return False
                
        except Exception as e:
            print(f"❌ 完成登录流程时出错: {e}")
            self.login_state = "failed"
            return False
    
    def run_complete_flow(self):
        """运行完整的自动登录流程"""
        try:
            print("=" * 70)
            print("🚀 XServer GAME 完全自动化登录流程")
            print("=" * 70)
            print()
            
            # 显示配置信息
            print("📋 当前配置:")
            print(f"   XServer邮箱: {XSERVER_EMAIL}")
            print(f"   XServer密码: {'*' * len(XSERVER_PASSWORD)}")
            print(f"   验证邮箱: {WEBMAIL_USERNAME}@zmkk.edu.kg")
            print(f"   邮箱密码: {'*' * len(WEBMAIL_PASSWORD)}")
            print(f"   无头模式: {USE_HEADLESS}")
            print(f"   运行环境: {'GitHub Actions' if IS_GITHUB_ACTIONS else '本地环境'}")
            print()
            
            # 验证基本配置
            if not XSERVER_EMAIL or not XSERVER_PASSWORD:
                print("❌ 请设置正确的XServer登录信息！")
                return False
            
            if not WEBMAIL_USERNAME or not WEBMAIL_PASSWORD:
                print("❌ 请设置正确的邮箱验证信息！")
                return False
            
            # 1. 初始化登录器
            print("📦 正在初始化登录组件...")
            if not self.create_xserver_login():
                return False
            
            if not self.create_webmail_login():
                return False
            
            # 2. 开始XServer登录流程
            result = self.start_xserver_login()
            
            if result == "need_verification":
                # 3. 需要验证码，自动获取
                code = self.wait_for_verification_code()
                
                if not code:
                    print("❌ 无法获取验证码，登录失败")
                    # 获取验证码失败也要清理邮箱浏览器
                    self.cleanup_webmail_only()
                    return False
                
                # 4. 输入验证码
                if not self.input_verification_code(code):
                    print("❌ 验证码输入失败")
                    # 即使失败也要清理邮箱浏览器
                    self.cleanup_webmail_only()
                    return False
                
                # 验证码输入成功，立即清理邮箱浏览器
                print("🧹 验证码输入完成，清理邮箱浏览器...")
                self.cleanup_webmail_only()
                
                # 5. 完成登录流程
                return self.complete_login_flow()
                
            elif result == True:
                # 直接登录成功
                print("✅ 直接登录成功，无需验证码")
                self.login_state = "completed"
                return True
            else:
                # 登录失败
                print("❌ XServer登录失败")
                return False
                
        except Exception as e:
            print(f"❌ 完整登录流程出错: {e}")
            return False
        finally:
            # 清理资源
            self.cleanup()
    
    def cleanup_webmail_only(self):
        """只清理邮箱登录器"""
        try:
            if self.webmail_login and self.webmail_login.driver:
                print("🧹 清理邮箱登录器...")
                self.webmail_login.cleanup()
        except Exception as e:
            print(f"⚠️ 清理邮箱资源时出错: {e}")
    
    def cleanup(self):
        """清理所有资源"""
        try:
            if self.xserver_login and self.xserver_login.driver:
                # 保持浏览器打开一段时间查看结果
                if self.login_state == "completed":
                    print("⏰ 浏览器将在 30 秒后关闭...")
                    time.sleep(30)
                self.xserver_login.cleanup()
            
            # 确保邮箱登录器也被清理
            self.cleanup_webmail_only()
                
        except Exception as e:
            print(f"⚠️ 清理资源时出错: {e}")

# =====================================================================
#                          主程序入口
# =====================================================================

def main():
    """主函数"""
    controller = XServerMainController()
    success = controller.run_complete_flow()
    
    if success:
        print("\n🎉 自动登录流程执行成功！")
        return 0
    else:
        print("\n❌ 自动登录流程执行失败！")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
