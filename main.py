#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XServer GAME 自动登录脚本
基于 undetected-chromedriver 实现绕过反机器人检测
支持自动验证码获取和手动输入两种模式
"""

import undetected_chromedriver as uc
import time
import re
import datetime
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# =====================================================================
#                          配置区域
# =====================================================================

# XServer登录信息配置 (支持环境变量)
LOGIN_EMAIL = os.getenv("XSERVER_EMAIL", "faiz555@zmkk.edu.kg")  # 请替换为您的邮箱
LOGIN_PASSWORD = os.getenv("XSERVER_PASSWORD", "faiz555!!")        # 请替换为您的密码

# 网站配置
TARGET_URL = "https://secure.xserver.ne.jp/xapanel/login/xmgame"

# 浏览器配置 (GitHub Actions中自动启用无头模式)
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
USE_HEADLESS = IS_GITHUB_ACTIONS or os.getenv("USE_HEADLESS", "false").lower() == "true"
WAIT_TIMEOUT = 10     # 页面元素等待超时时间（秒）
PAGE_LOAD_DELAY = 3   # 页面加载延迟时间（秒）

# 验证码处理配置 (支持环境变量)
AUTO_VERIFICATION = os.getenv("AUTO_VERIFICATION", "true").lower() == "true"  # 自动从邮箱获取验证码

# 邮箱自动验证配置 (支持环境变量)
WEBMAIL_URL = "https://zmkk.edu.kg/login"  # 网页邮箱地址
WEBMAIL_USERNAME = os.getenv("WEBMAIL_USERNAME", "kaixa913")             # 邮箱用户名
WEBMAIL_PASSWORD = os.getenv("WEBMAIL_PASSWORD", "kaixa913!!")           # 邮箱密码
TARGET_MAILBOX = os.getenv("TARGET_MAILBOX", "faiz555@zmkk.edu.kg")    # 目标邮箱地址

# =====================================================================
#                        XServer 自动登录类
# =====================================================================

class XServerAutoLogin:
    """XServer GAME 自动登录主类"""
    
    def __init__(self):
        """
        初始化 XServer GAME 自动登录器
        使用配置区域的设置
        """
        self.driver = None
        self.headless = USE_HEADLESS
        self.email = LOGIN_EMAIL
        self.password = LOGIN_PASSWORD
        self.target_url = TARGET_URL
        self.wait_timeout = WAIT_TIMEOUT
        self.page_load_delay = PAGE_LOAD_DELAY
        self.screenshot_count = 0  # 截图计数器
        
        # 邮箱验证相关配置
        self.auto_verification = AUTO_VERIFICATION
        self.webmail_url = WEBMAIL_URL
        self.webmail_username = WEBMAIL_USERNAME
        self.webmail_password = WEBMAIL_PASSWORD
        self.target_mailbox = TARGET_MAILBOX
    
    # =================================================================
    #                       1. 浏览器管理模块
    # =================================================================
    
    def setup_driver(self):
        """设置 Chrome 驱动"""
        try:
            # 配置 Chrome 选项
            options = uc.ChromeOptions()
            
            if self.headless:
                options.add_argument('--headless')
            
            # 添加基本的Chrome选项（undetected-chromedriver兼容）
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-notifications')
            options.add_argument('--window-size=1920,1080')
            
            # 创建 undetected Chrome 实例（它会自动处理反检测）
            self.driver = uc.Chrome(options=options)
            self.driver.maximize_window()
            
            print("✅ Chrome 驱动初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ Chrome 驱动初始化失败: {e}")
            return False
    
    def take_screenshot(self, step_name=""):
        """截图功能 - 用于可视化调试"""
        try:
            if self.driver:
                self.screenshot_count += 1
                timestamp = datetime.datetime.now().strftime("%H%M%S")
                filename = f"step_{self.screenshot_count:02d}_{timestamp}_{step_name}.png"
                
                # 确保文件名安全
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                
                self.driver.save_screenshot(filename)
                print(f"📸 截图已保存: {filename}")
                return filename
        except Exception as e:
            print(f"⚠️ 截图失败: {e}")
        return None
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            try:
                self.driver.quit()
                print("🧹 浏览器已关闭")
            except Exception as e:
                print(f"⚠️ 关闭浏览器时出错: {e}")
    
    # =================================================================
    #                       2. XServer登录模块
    # =================================================================
    
    def navigate_to_login(self):
        """导航到登录页面"""
        try:
            print(f"🌐 正在访问: {self.target_url}")
            self.driver.get(self.target_url)
            
            # 等待页面加载
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            print("✅ 页面加载成功")
            self.take_screenshot("login_page_loaded")
            return True
            
        except TimeoutException:
            print("❌ 页面加载超时")
            return False
        except Exception as e:
            print(f"❌ 导航失败: {e}")
            return False
    
    def find_login_form(self):
        """查找登录表单元素"""
        try:
            print("🔍 正在查找登录表单...")
            
            # 等待页面加载完成
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
            
            # 查找邮箱输入框
            try:
                email_input = self.driver.find_element(By.XPATH, "//input[@name='memberid']")
                print("✅ 找到邮箱输入框: //input[@name='memberid']")
            except Exception:
                print("❌ 未找到邮箱输入框")
                email_input = None

            # 查找密码输入框
            try:
                password_input = self.driver.find_element(By.XPATH, "//input[@name='user_password']")
                print("✅ 找到密码输入框: //input[@name='user_password']")
            except Exception:
                print("❌ 未找到密码输入框")
                password_input = None

            # 查找登录按钮
            try:
                login_button = self.driver.find_element(By.XPATH, "//input[@value='ログインする']")
                print("✅ 找到登录按钮: //input[@value='ログインする']")
            except Exception:
                print("⚠️ 未找到登录按钮，将尝试使用回车键提交")
                login_button = None

            if not email_input or not password_input:
                return None, None, None
            
            return email_input, password_input, login_button
            
        except Exception as e:
            print(f"❌ 查找登录表单时出错: {e}")
            return None, None, None
    
    def perform_login(self):
        """执行登录操作"""
        try:
            # 查找登录表单元素
            email_input, password_input, login_button = self.find_login_form()
            
            if not email_input or not password_input:
                return False
            
            print("📝 正在填写登录信息...")
            
            # 模拟人类行为：慢速输入邮箱
            email_input.clear()
            self.human_type(email_input, self.email)
            print("✅ 邮箱已填写")
            
            # 等待一下，模拟人类思考时间
            time.sleep(2)
            
            # 模拟人类行为：慢速输入密码
            password_input.clear()
            self.human_type(password_input, self.password)
            print("✅ 密码已填写")
            
            # 等待一下，模拟人类操作
            time.sleep(2)
            
            # 提交表单
            if login_button:
                print("🖱️ 点击登录按钮...")
                login_button.click()
            else:
                print("⌨️ 使用回车键提交...")
                password_input.send_keys("\n")
            
            print("✅ 登录表单已提交")
            
            # 等待页面响应
            time.sleep(3)
            
            return True
            
        except Exception as e:
            print(f"❌ 执行登录操作失败: {e}")
            return False
    
    def human_type(self, element, text):
        """模拟人类输入行为"""
        import random
        
        for char in text:
            element.send_keys(char)
            # 随机延迟，模拟真实的打字速度
            delay = random.uniform(0.05, 0.2)
            time.sleep(delay)
    
    # =================================================================
    #                       3. 验证码处理模块
    # =================================================================
    
    def handle_verification_page(self):
        """处理验证页面"""
        try:
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            # 检查是否是XServer的新环境验证页面
            self.take_screenshot("checking_verification_page")
            
            print(f"📍 当前URL: {current_url}")
            
            # 检查特定的验证页面URL和文字内容
            verification_url = "https://secure.xserver.ne.jp/xapanel/myaccount/loginauth/index"
            new_environment_text = "新しい環境からのログイン"
            
            url_matches = verification_url in current_url
            text_matches = new_environment_text in page_source
            
            print(f"🔍 URL匹配检查: {url_matches} (查找: {verification_url})")
            print(f"🔍 文字匹配检查: {text_matches} (查找: {new_environment_text})")
            
            is_verification_page = url_matches and text_matches
            
            if is_verification_page:
                print("🔐 检测到XServer新环境验证页面！")
                print("⚠️ 这是XServer的安全机制，检测到新环境登录")
                print()
                
                # 点击发送验证码按钮
                print("🔍 正在查找'認証コードを送信'按钮...")
                try:
                    send_code_button = self.driver.find_element(By.XPATH, "//input[@type='submit'][@value='認証コードを送信']")
                    print("✅ 找到发送验证码按钮")
                    send_code_button.click()
                    print("📧 已点击发送验证码按钮，验证码正在发送到您的邮箱")
                    time.sleep(5)  # 等待页面跳转和加载
                    
                    # 检查是否跳转到验证码输入页面
                    return self.handle_code_input_page()
                    
                except Exception as e:
                    print(f"❌ 未找到发送验证码按钮: {e}")
                    return False
            else:
                print("ℹ️ 当前页面不是验证页面")
                if not url_matches:
                    print("   - URL不匹配验证页面格式")
                if not text_matches:
                    print("   - 页面中未找到'新しい環境からのログイン'文字")
            
            return False
            
        except Exception as e:
            print(f"❌ 处理验证页面时出错: {e}")
            return False
    
    def handle_code_input_page(self):
        """处理验证码输入页面"""
        try:
            print("🔍 检查是否跳转到验证码输入页面...")
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            print(f"📍 当前URL: {current_url}")
            
            # 检查是否跳转到验证码输入页面
            code_input_url = "https://secure.xserver.ne.jp/xapanel/myaccount/loginauth/smssend"
            prompt_text = "メールアドレス宛にお送りした認証コードを入力してください"
            
            url_matches = code_input_url in current_url
            text_matches = prompt_text in page_source
            
            print(f"🔍 URL匹配检查: {url_matches} (查找: {code_input_url})")
            print(f"🔍 提示文字检查: {text_matches} (查找: {prompt_text})")
            
            if url_matches and text_matches:
                print("✅ 成功跳转到验证码输入页面！")
                print("📧 请检查您的邮箱获取验证码")
                print()
                
                # 查找验证码输入框
                print("🔍 正在查找验证码输入框...")
                try:
                    code_input = self.driver.find_element(By.XPATH, "//input[@id='auth_code'][@name='auth_code']")
                    print("✅ 找到验证码输入框")
                    
                    # 根据配置选择验证码获取方式
                    verification_code = None
                    
                    if self.auto_verification:
                        print("⏰ 等待30秒让验证码邮件送达...")
                        time.sleep(30)
                        
                        print("🤖 正在自动获取验证码...")
                        verification_code = self.auto_get_verification_code()
                        
                        if not verification_code:
                            print("❌ 自动获取验证码失败")
                            return False
                    else:
                        # 必须启用自动验证
                        print("❌ 需要启用AUTO_VERIFICATION=true自动获取验证码")
                        return False
                    
                    if verification_code:
                        code_input.clear()
                        self.human_type(code_input, verification_code)
                        print("✅ 验证码已输入")
                        
                        # 查找并点击登录按钮
                        print("🔍 正在查找ログイン按钮...")
                        try:
                            login_submit_button = self.driver.find_element(By.XPATH, "//input[@type='submit'][@value='ログイン']")
                            print("✅ 找到ログイン按钮")
                            login_submit_button.click()
                            print("✅ 验证码已提交")
                            
                            # 等待验证结果
                            time.sleep(5)
                            return True
                            
                        except Exception as e:
                            print(f"❌ 未找到ログイン按钮: {e}")
                            return False
                    else:
                        print("❌ 未输入验证码")
                        return False
                
                except Exception as e:
                    print(f"❌ 未找到验证码输入框: {e}")
                    return False
            else:
                print("❌ 未成功跳转到验证码输入页面")
                if not url_matches:
                    print("   - URL不匹配验证码输入页面")
                if not text_matches:
                    print("   - 页面中未找到预期的提示文字")
                return False
            
        except Exception as e:
            print(f"❌ 处理验证码输入页面时出错: {e}")
            return False
    
    # =================================================================
    #                       4. 邮箱自动验证模块
    # =================================================================
    
    def auto_get_verification_code(self):
        """自动从邮箱获取验证码"""
        try:
            print("🤖 开始自动获取验证码...")
            
            # 保存当前窗口句柄
            main_window = self.driver.current_window_handle
            
            # 打开新标签页
            self.driver.execute_script("window.open('');")
            all_windows = self.driver.window_handles
            new_window = [w for w in all_windows if w != main_window][0]
            
            # 切换到新标签页
            self.driver.switch_to.window(new_window)
            print("📂 已打开新标签页用于邮箱登录")
            
            # 访问邮箱
            if not self.webmail_login():
                self.driver.close()
                self.driver.switch_to.window(main_window)
                return None
            
            # 获取验证码
            verification_code = self.get_verification_from_email()
            
            # 关闭邮箱标签页
            self.driver.close()
            
            # 切换回主标签页
            self.driver.switch_to.window(main_window)
            print("🔙 已返回验证码输入页面")
            
            return verification_code
            
        except Exception as e:
            print(f"❌ 自动获取验证码失败: {e}")
            # 确保切换回主窗口
            try:
                self.driver.switch_to.window(main_window)
            except:
                pass
            return None
    
    def webmail_login(self):
        """邮箱登录"""
        try:
            print(f"🌐 正在访问邮箱: {self.webmail_url}")
            self.driver.get(self.webmail_url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 查找并填写邮箱登录表单
            try:
                email_input = self.driver.find_element(By.XPATH, "//input[@placeholder='邮箱']")
                password_input = self.driver.find_element(By.XPATH, "//input[@placeholder='密码']")
                login_button = self.driver.find_element(By.XPATH, "//button[@class='el-button el-button--primary btn']")
                
                print("📝 正在填写邮箱登录信息...")
                email_input.clear()
                self.human_type(email_input, self.webmail_username)
                
                time.sleep(1)
                
                password_input.clear()
                self.human_type(password_input, self.webmail_password)
                
                time.sleep(1)
                
                login_button.click()
                print("✅ 邮箱登录表单已提交")
                
                # 等待登录完成
                time.sleep(5)
                
                # 选择目标邮箱
                return self.select_target_mailbox()
                
            except Exception as e:
                print(f"❌ 邮箱登录失败: {e}")
                return False
                
        except Exception as e:
            print(f"❌ 访问邮箱失败: {e}")
            return False
    
    def select_target_mailbox(self):
        """选择目标邮箱"""
        try:
            print("📧 正在选择目标邮箱...")
            time.sleep(3)
            
            mailbox_element = self.driver.find_element(By.XPATH, f"//div[@class='account' and contains(text(), '{self.target_mailbox}')]")
            mailbox_element.click()
            print(f"✅ 已选择 {self.target_mailbox} 邮箱")
            
            time.sleep(5)
            return True
            
        except Exception as e:
            print(f"❌ 选择邮箱失败: {e}")
            return False
    
    def get_verification_from_email(self):
        """从邮件中提取验证码"""
        try:
            print("🔍 正在搜索验证码邮件...")
            
            # 刷新页面确保获取最新邮件
            self.driver.refresh()
            time.sleep(5)
            
            # 查找XServer验证码邮件
            email_selectors = [
                "//*[contains(text(), '【XServerアカウント】ログイン用認証コードのお知らせ')]",
                "//*[contains(text(), 'XServerアカウント') and contains(text(), 'ログイン用認証コード')]",
                "//*[contains(text(), 'ログイン用認証コードのお知らせ')]"
            ]
            
            email_element = None
            for selector in email_selectors:
                try:
                    email_elements = self.driver.find_elements(By.XPATH, selector)
                    if email_elements:
                        email_element = email_elements[0]  # 取最新的
                        print("✅ 找到验证码邮件")
                        break
                except:
                    continue
            
            if not email_element:
                print("❌ 未找到验证码邮件")
                return None
            
            # 点击邮件
            email_element.click()
            time.sleep(3)
            
            # 提取验证码
            page_source = self.driver.page_source
            
            # 使用正则表达式提取验证码
            code_patterns = [
                r'【認証コード】[　\s]*：[　\s]*(\d{4,8})',
                r'【認証コード】[　\s]*[：:][　\s]*(\d{4,8})',
                r'認証コード[　\s]*[：:][　\s]*(\d{4,8})'
            ]
            
            for pattern in code_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE | re.MULTILINE)
                if matches:
                    valid_codes = [code for code in matches if len(code) >= 4 and len(code) <= 8]
                    if valid_codes:
                        verification_code = valid_codes[0]
                        print(f"✅ 成功提取验证码: {verification_code}")
                        
                        # 尝试复制到剪贴板
                        try:
                            import pyperclip
                            pyperclip.copy(verification_code)
                            print("📋 验证码已复制到剪贴板")
                        except:
                            print("ℹ️ 无法复制到剪贴板")
                        
                        return verification_code
            
            print("❌ 未能提取到验证码")
            return None
            
        except Exception as e:
            print(f"❌ 提取验证码失败: {e}")
            return None
    
    # =================================================================
    #                       5. 登录结果处理模块
    # =================================================================
    
    def handle_login_result(self):
        """处理登录结果"""
        try:
            print("🔍 正在检查登录结果...")
            
            # 等待页面加载
            time.sleep(3)
            
            current_url = self.driver.current_url
            print(f"📍 当前URL: {current_url}")
            
            # 简单直接：只判断是否跳转到成功页面
            success_url = "https://secure.xserver.ne.jp/xapanel/xmgame/index"
            
            if current_url == success_url:
                print("✅ 登录成功！已跳转到XServer GAME管理页面")
                
                # 等待5秒后跳转到游戏管理页面
                print("⏰ 等待5秒后跳转到游戏管理页面...")
                time.sleep(5)
                
                # 跳转到游戏管理页面
                game_url = "https://secure.xserver.ne.jp/xmgame/game/index"
                print(f"🎮 正在跳转到游戏管理页面: {game_url}")
                self.driver.get(game_url)
                
                # 等待页面加载并验证跳转
                time.sleep(3)
                final_url = self.driver.current_url
                print(f"📍 最终页面URL: {final_url}")
                
                if final_url == game_url:
                    print("✅ 成功跳转到游戏管理页面")
                    self.take_screenshot("game_page_loaded")
                else:
                    print(f"⚠️ 跳转到游戏页面可能失败")
                    print(f"   预期URL: {game_url}")
                    print(f"   实际URL: {final_url}")
                
                return True
            else:
                print(f"❌ 登录失败！当前URL不是预期的成功页面")
                print(f"   预期URL: {success_url}")
                print(f"   实际URL: {current_url}")
                return False
            
        except Exception as e:
            print(f"❌ 检查登录结果时出错: {e}")
            return False
    
    # =================================================================
    #                       6. 配置验证模块
    # =================================================================
    
    def validate_config(self):
        """验证配置信息"""
        try:
            if not self.email or self.email == "your_email@example.com":
                print("❌ 请在配置区域设置正确的邮箱地址")
                return False
            
            if not self.password or self.password == "your_password":
                print("❌ 请在配置区域设置正确的密码")
                return False
            
            print("✅ 配置信息验证通过")
            return True
            
        except Exception as e:
            print(f"❌ 验证配置时出错: {e}")
            return False
    
    # =================================================================
    #                       7. 主流程控制模块
    # =================================================================
    
    def run(self):
        """运行自动登录流程"""
        try:
            print("🚀 开始 XServer GAME 自动登录流程...")
            
            # 步骤1：验证配置
            if not self.validate_config():
                return False
            
            # 步骤2：设置驱动
            if not self.setup_driver():
                return False
            
            # 步骤3：导航到登录页面
            if not self.navigate_to_login():
                return False
            
            # 步骤4：执行登录操作
            if not self.perform_login():
                return False
            
            # 步骤5：检查是否需要验证
            if self.handle_verification_page():
                print("✅ 验证流程已处理")
                time.sleep(3)  # 等待验证完成后的页面跳转
            
            # 步骤6：检查登录结果
            if not self.handle_login_result():
                print("⚠️ 登录可能失败，请检查邮箱和密码是否正确")
                return False
            
            print("🎉 XServer GAME 自动登录流程完成！")
            self.take_screenshot("login_completed")
            
            # 保持浏览器打开一段时间以便查看结果
            print("⏰ 浏览器将在 30 秒后关闭...")
            time.sleep(30)
            
            return True
            
        except Exception as e:
            print(f"❌ 自动登录流程出错: {e}")
            return False
        
        finally:
            self.cleanup()


# =====================================================================
#                          主程序入口
# =====================================================================

def main():
    """主函数"""
    print("=" * 60)
    print("XServer GAME 自动登录脚本")
    print("基于 undetected-chromedriver")
    print("=" * 60)
    print()
    
    # 显示当前配置
    print("📋 当前配置:")
    print(f"   XServer邮箱: {LOGIN_EMAIL}")
    print(f"   XServer密码: {'*' * len(LOGIN_PASSWORD)}")
    print(f"   目标网站: {TARGET_URL}")
    print(f"   无头模式: {USE_HEADLESS}")
    print(f"   自动验证: {AUTO_VERIFICATION}")
    if AUTO_VERIFICATION:
        print(f"   邮箱地址: {WEBMAIL_URL}")
        print(f"   邮箱用户: {WEBMAIL_USERNAME}")
        print(f"   目标邮箱: {TARGET_MAILBOX}")
    print()
    
    # 确认配置
    if LOGIN_EMAIL == "your_email@example.com" or LOGIN_PASSWORD == "your_password":
        print("❌ 请先在代码开头的配置区域设置正确的邮箱和密码！")
        return
    
    print("🚀 配置验证通过，自动开始登录...")
    
    # 创建并运行自动登录器
    auto_login = XServerAutoLogin()
    success = auto_login.run()
    
    if success:
        print("✅ 登录流程执行成功！")
    else:
        print("❌ 登录流程执行失败！")


# =====================================================================
#                          程序启动点
# =====================================================================

if __name__ == "__main__":
    main()