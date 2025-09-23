#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XServer GAME 自动登录主控脚本
联动 login.py 和 code.py 实现完全自动化的登录流程
"""

import os
import sys
import time
from pathlib import Path

# 导入自定义脚本模块
from login import XServerAutoLogin
from code import WebmailAutoLogin

# 导入Selenium组件
from selenium.webdriver.common.by import By

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
    
    def get_verification_code_in_new_tab(self):
        """在XServer浏览器中新开标签页获取验证码"""
        try:
            print("📧 开始在新标签页获取邮箱验证码...")
            
            # 等待一段时间让验证码邮件发送
            print("⏰ 等待验证码邮件发送...")
            time.sleep(30)
            
            # 保存当前XServer标签页
            original_window = self.xserver_login.driver.current_window_handle
            print(f"💾 保存XServer标签页: {original_window}")
            
            # 在当前浏览器中新开标签页
            print("🆕 打开新标签页用于邮箱登录...")
            self.xserver_login.driver.execute_script("window.open('');")
            
            # 切换到新标签页
            all_windows = self.xserver_login.driver.window_handles
            new_window = [w for w in all_windows if w != original_window][0]
            self.xserver_login.driver.switch_to.window(new_window)
            print(f"🔄 已切换到新标签页: {new_window}")
            
            # 使用XServer的浏览器实例进行邮箱登录
            driver = self.xserver_login.driver
            
            # 导航到邮箱登录页面
            print(f"🌐 正在访问邮箱: {WEBMAIL_URL}")
            driver.get(WEBMAIL_URL)
            time.sleep(3)
            print("✅ 邮箱页面加载成功")
            
            # 执行邮箱登录
            if self.perform_webmail_login_in_tab(driver):
                # 获取验证码
                code = self.extract_verification_code_in_tab(driver)
                
                # 关闭邮箱标签页
                print("🗑️ 关闭邮箱标签页...")
                driver.close()
                
                # 切换回XServer标签页
                self.xserver_login.driver.switch_to.window(original_window)
                print("🔙 已切换回XServer标签页")
                
                return code
            else:
                # 登录失败，关闭标签页
                driver.close()
                self.xserver_login.driver.switch_to.window(original_window)
                return None
                
        except Exception as e:
            print(f"❌ 在新标签页获取验证码失败: {e}")
            try:
                # 确保切换回原标签页
                self.xserver_login.driver.switch_to.window(original_window)
            except:
                pass
            return None
    
    def perform_webmail_login_in_tab(self, driver):
        """在标签页中执行邮箱登录"""
        try:
            print("🔍 正在查找邮箱登录表单...")
            time.sleep(3)  # 等待页面加载
            
            # 查找邮箱输入框
            email_input = driver.find_element(By.XPATH, "//input[@placeholder='邮箱']")
            print("✅ 找到邮箱输入框")
            
            # 查找密码输入框
            password_input = driver.find_element(By.XPATH, "//input[@placeholder='密码']")
            print("✅ 找到密码输入框")
            
            # 查找登录按钮
            login_button = driver.find_element(By.XPATH, "//button[@class='el-button el-button--primary btn']")
            print("✅ 找到登录按钮")
            
            # 填写登录信息
            print("📝 正在填写邮箱登录信息...")
            email_input.clear()
            email_input.send_keys(WEBMAIL_USERNAME)
            print("✅ 邮箱已填写")
            
            time.sleep(2)
            password_input.clear()
            password_input.send_keys(WEBMAIL_PASSWORD)
            print("✅ 密码已填写")
            
            # 点击登录
            time.sleep(2)
            login_button.click()
            print("✅ 登录表单已提交")
            
            # 等待登录结果
            time.sleep(5)
            
            # 检查是否登录成功
            current_url = driver.current_url
            if "email" in current_url:
                print("✅ 邮箱登录成功！")
                return True
            else:
                print("❌ 邮箱登录失败")
                return False
                
        except Exception as e:
            print(f"❌ 邮箱登录过程出错: {e}")
            return False
    
    def extract_verification_code_in_tab(self, driver):
        """在标签页中提取验证码"""
        try:
            print("📧 正在选择目标邮箱...")
            
            # 选择目标邮箱
            target_mailbox = driver.find_element(By.XPATH, f"//div[@class='account' and contains(text(), '{WEBMAIL_USERNAME}')]")
            target_mailbox.click()
            print(f"✅ 已选择 {WEBMAIL_USERNAME} 邮箱")
            
            time.sleep(3)
            
            # 搜索XServer验证码邮件
            print("🔍 正在搜索XServer验证码邮件...")
            
            # 滚动页面加载所有邮件
            print("📜 正在滚动页面加载所有邮件...")
            for i in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            print("✅ 页面滚动完成，邮件列表已加载")
            
            # 查找XServer邮件
            xserver_emails = driver.find_elements(By.XPATH, "//div[contains(text(), 'XServerアカウント') and contains(text(), 'ログイン用認証コード')]")
            
            if xserver_emails:
                print(f"✅ 找到 {len(xserver_emails)} 封XServer邮件")
                
                # 点击第一封（最新的）邮件
                first_email = xserver_emails[0]
                first_email.click()
                print("🎯 正在打开最新的XServerアカウント邮件...")
                time.sleep(3)
                
                # 提取验证码
                page_source = driver.page_source
                
                # 使用code.py中的验证码提取逻辑
                import re
                code_patterns = [
                    r'【認証コード】[　\s]*：[　\s]*(\d{4,8})',
                    r'【認証コード】[　\s]*[：:][　\s]*(\d{4,8})',
                    r'認証コード[　\s]*[：:][　\s]*(\d{4,8})',
                ]
                
                for pattern in code_patterns:
                    matches = re.findall(pattern, page_source, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        valid_codes = [code for code in matches if len(code) >= 4 and len(code) <= 8]
                        if valid_codes:
                            verification_code = valid_codes[0]
                            print(f"✅ 找到验证码: {verification_code}")
                            return verification_code
                
                print("❌ 未能从邮件中提取到验证码")
                return None
            else:
                print("❌ 未找到XServer验证码邮件")
                return None
                
        except Exception as e:
            print(f"❌ 提取验证码失败: {e}")
            return None
    
    def wait_for_verification_code(self, timeout=VERIFICATION_TIMEOUT):
        """获取验证码（在XServer浏览器新标签页中处理）"""
        try:
            print(f"🔍 开始获取验证码（新标签页模式）...")
            
            # 在XServer浏览器新标签页中获取验证码
            code = self.get_verification_code_in_new_tab()
            
            if code:
                print(f"✅ 成功获取验证码: {code}")
                self.verification_code = code
                return code
            else:
                print("❌ 验证码获取失败")
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
                    return False
                
                # 4. 输入验证码（邮箱浏览器已在获取验证码后清理）
                if not self.input_verification_code(code):
                    print("❌ 验证码输入失败")
                    return False
                
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
    
    def cleanup(self):
        """清理所有资源"""
        try:
            if self.xserver_login and self.xserver_login.driver:
                # 保持浏览器打开一段时间查看结果
                if self.login_state == "completed":
                    print("⏰ 浏览器将在 30 秒后关闭...")
                    time.sleep(30)
                self.xserver_login.cleanup()
                
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
