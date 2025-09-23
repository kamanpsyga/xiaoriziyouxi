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
            
            # 字体和语言支持
            options.add_argument('--lang=ja-JP')  # 设置日语环境
            options.add_argument('--accept-lang=ja-JP,ja,en-US,en')
            
            # 字体设置，确保日文正确显示
            prefs = {
                "intl.accept_languages": "ja-JP,ja,en-US,en",
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0
            }
            options.add_experimental_option("prefs", prefs)
            
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
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("✅ 邮箱页面加载成功")
            
            # 执行登录
            if not self.perform_webmail_login():
                return False
            
            # 检查登录结果
            if not self.check_webmail_login_result():
                print("⚠️ 邮箱登录可能失败")
                return False
            
            print("🎉 邮箱登录成功！")
            
            # 选择目标邮箱
            return self.select_target_mailbox()
                
        except Exception as e:
            print(f"❌ 访问邮箱失败: {e}")
            return False
    
    def find_webmail_login_form(self):
        """查找邮箱登录表单"""
        try:
            print("🔍 正在查找登录表单...")
            
            # 等待页面完全加载
            print("⏰ 等待页面完全加载...")
            time.sleep(5)
            
            # 打印页面信息用于调试
            print(f"📍 当前URL: {self.driver.current_url}")
            print(f"📄 页面标题: {self.driver.title}")
            
            # 检查页面是否包含预期元素
            page_source = self.driver.page_source
            if "邮箱" in page_source or "email" in page_source.lower():
                print("✅ 页面包含邮箱相关内容")
            else:
                print("⚠️ 页面可能未完全加载或结构不同")
            
            # 登录部分已确定，保持简化
            email_selectors = [
                "//input[@placeholder='邮箱']",   # 已确定有效
            ]

            password_selectors = [
                "//input[@placeholder='密码']",   # 已确定有效
            ]

            login_selectors = [
                "//button[@class='el-button el-button--primary btn']",  # 已确定有效
            ]
            
            # 查找邮箱输入框
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = self.driver.find_element(By.XPATH, selector)
                    print(f"✅ 找到邮箱输入框: {selector}")
                    break
                except:
                    continue
            
            # 查找密码输入框
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.XPATH, selector)
                    print(f"✅ 找到密码输入框: {selector}")
                    break
                except:
                    continue
            
            # 查找登录按钮
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = self.driver.find_element(By.XPATH, selector)
                    print(f"✅ 找到登录按钮: {selector}")
                    break
                except:
                    continue
            
            if not email_input:
                print("❌ 未找到邮箱输入框")
                return None, None, None
            
            if not password_input:
                print("❌ 未找到密码输入框")
                return None, None, None
            
            if not login_button:
                print("⚠️ 未找到登录按钮，将尝试使用回车键提交")
            
            return email_input, password_input, login_button
            
        except Exception as e:
            print(f"❌ 查找登录表单失败: {e}")
            return None, None, None
    
    def perform_webmail_login(self):
        """执行邮箱登录"""
        try:
            # 查找登录表单
            email_input, password_input, login_button = self.find_webmail_login_form()
            
            if not email_input or not password_input:
                return False
            
            print("📝 正在填写登录信息...")
            
            # 填写邮箱
            email_input.clear()
            self.human_type(email_input, self.webmail_username)
            print("✅ 邮箱已填写")
            
            # 等待一下
            time.sleep(1)
            
            # 填写密码
            password_input.clear()
            self.human_type(password_input, self.webmail_password)
            print("✅ 密码已填写")
            
            # 等待一下
            time.sleep(1)
            
            # 提交登录
            if login_button:
                print("🖱️ 点击登录按钮...")
                login_button.click()
            else:
                print("⌨️ 使用回车键提交...")
                password_input.send_keys("\n")
            
            print("✅ 登录表单已提交")
            
            # 等待页面响应
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"❌ 执行登录失败: {e}")
            return False
    
    def check_webmail_login_result(self):
        """检查邮箱登录结果"""
        try:
            print("🔍 正在检查登录结果...")
            
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title
            
            print(f"📍 当前URL: {current_url}")
            print(f"📄 页面标题: {page_title}")
            
            # 首先检查是否跳转到邮箱页面（明确的成功标识）
            if "zmkk.edu.kg/email" in current_url:
                print("✅ 成功跳转到邮箱页面，登录成功！")
                return True
            
            # 检查是否有错误信息
            error_indicators = [
                "error", "错误", "失败", "incorrect", "invalid", 
                "wrong", "密码错误", "用户名错误", "登录失败"
            ]
            
            for indicator in error_indicators:
                if indicator in page_source:
                    print(f"❌ 检测到错误信息: {indicator}")
                    return False
            
            # 检查其他成功标识
            success_indicators = [
                "inbox", "收件箱", "邮箱", "mailbox", "mail", 
                "welcome", "欢迎", "dashboard", "控制面板"
            ]
            
            for indicator in success_indicators:
                if indicator in page_source or indicator in page_title.lower():
                    print(f"✅ 检测到成功标识: {indicator}")
                    return True
            
            # 检查URL变化（不在登录页面）
            if current_url != self.webmail_url.lower() and "login" not in current_url:
                print("✅ URL已改变，登录可能成功")
                return True
            
            # 如果还在登录页面
            if "login" in current_url:
                print("⚠️ 仍在登录页面，登录可能失败")
                return False
            
            print("✅ 登录状态检查完成")
            return True
            
        except Exception as e:
            print(f"❌ 检查登录结果失败: {e}")
            return False
    
    def select_target_mailbox(self):
        """选择目标邮箱 faiz555@zmkk.edu.kg"""
        try:
            print("📧 正在选择目标邮箱...")
            
            # 等待邮箱列表加载
            time.sleep(3)
            
            # 邮箱选择已确定，保持简化
            mailbox_selectors = [
                "//div[@class='account' and contains(text(), 'faiz555@zmkk.edu.kg')]",  # 已确定有效
            ]
            
            mailbox_element = None
            for selector in mailbox_selectors:
                try:
                    mailbox_element = self.driver.find_element(By.XPATH, selector)
                    print(f"✅ 找到目标邮箱: {selector}")
                    break
                except:
                    continue
            
            if not mailbox_element:
                print("❌ 未找到 faiz555@zmkk.edu.kg 邮箱")
                return False
            
            # 点击进入邮箱
            mailbox_element.click()
            print("✅ 已选择 faiz555@zmkk.edu.kg 邮箱")
            
            # 等待邮箱内容加载
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"❌ 选择邮箱失败: {e}")
            return False
    
    def scroll_to_load_emails(self):
        """滚动页面确保所有邮件都加载完成"""
        try:
            # 获取当前页面高度
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # 滚动几次确保邮件列表完全加载
            for i in range(3):
                # 滚动到页面底部
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # 检查是否有新内容加载
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # 滚动回到顶部
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            print("✅ 页面滚动完成，邮件列表已加载")
            
        except Exception as e:
            print(f"⚠️ 滚动页面失败: {e}")

    def search_verification_email(self):
        """搜索验证码邮件"""
        try:
            print("🔍 正在搜索XServer验证码邮件...")
            
            # 等待邮箱页面完全加载
            time.sleep(3)
            
            # 尝试刷新收件箱
            refresh_selectors = [
                "//button[contains(text(), '刷新')]",
                "//button[contains(text(), 'Refresh')]",
                "//button[contains(@class, 'refresh')]",
                "//i[contains(@class, 'refresh')]/parent::button"
            ]
            
            for selector in refresh_selectors:
                try:
                    refresh_btn = self.driver.find_element(By.XPATH, selector)
                    refresh_btn.click()
                    print("✅ 已刷新收件箱")
                    time.sleep(2)
                    break
                except:
                    continue
            
            # 精确定位验证码邮件 - 查找完整的邮件标题
            email_selectors = [
                # 最精确的选择器 - 完整的邮件标题
                "//*[contains(text(), '【XServerアカウント】ログイン用認証コードのお知らせ')]",
                
                # 备用选择器 - 分段匹配
                "//*[contains(text(), 'XServerアカウント') and contains(text(), 'ログイン用認証コード')]",
                "//*[contains(text(), 'ログイン用認証コードのお知らせ')]",
                "//*[contains(text(), '認証コード') and contains(text(), 'お知らせ')]",
            ]
            
            # 滚动页面确保所有邮件都加载完成
            print("📜 正在滚动页面加载所有邮件...")
            self.scroll_to_load_emails()
            
            # 统计所有找到的XServer邮件
            print("🔍 正在统计所有XServerアカウント邮件...")
            
            all_xserver_emails = []
            successful_selectors = []
            
            # 使用优化后的选择器查找邮件
            for selector in email_selectors:
                try:
                    emails = self.driver.find_elements(By.XPATH, selector)
                    if emails:
                        # 去重：避免同一封邮件被多个选择器重复找到
                        unique_emails = []
                        for email in emails:
                            if email not in all_xserver_emails:
                                unique_emails.append(email)
                                all_xserver_emails.append(email)
                        
                        if unique_emails:
                            print(f"✅ 找到 {len(unique_emails)} 封新的XServer邮件")
                            successful_selectors.append(selector)
                        
                except Exception as e:
                    print(f"⚠️ 选择器查找失败: {e}")
                    continue
            
            # 显示统计结果
            print(f"\n📊 统计结果:")
            print(f"   🎯 总共找到: {len(all_xserver_emails)} 封XServerアカウント邮件")
            print(f"   ✅ 有效选择器: {len(successful_selectors)} 个")
            
            if all_xserver_emails:
                print(f"   📧 邮件列表:")
                for i, email in enumerate(all_xserver_emails[:5], 1):  # 只显示前5封
                    try:
                        email_text = email.text.strip()[:100]  # 截取前100个字符
                        print(f"      {i}. {email_text}...")
                    except:
                        print(f"      {i}. [无法获取邮件文本]")
                
                if len(all_xserver_emails) > 5:
                    print(f"      ... 还有 {len(all_xserver_emails) - 5} 封邮件")
                
                # 点击第一封邮件（最新的）
                print(f"\n🎯 正在打开第一封（最新的）XServerアカウント邮件...")
                try:
                    first_email = all_xserver_emails[0]
                    first_email.click()
                    print("✅ 已成功打开最新的XServerアカウント邮件")
                    time.sleep(3)
                    return True
                except Exception as e:
                    print(f"❌ 点击邮件失败: {e}")
                    return False
            else:
                print("   ❌ 未找到任何XServerアカウント邮件")
                return False
                
        except Exception as e:
            print(f"❌ 搜索验证邮件失败: {e}")
            return False
    
    def extract_verification_code(self):
        """从邮件内容中提取验证码"""
        try:
            print("🔍 正在提取验证码...")
            
            # 获取页面内容
            page_source = self.driver.page_source
            
            # 根据日志确定的有效验证码匹配模式
            code_patterns = [
                # 主要模式 - 日志显示成功的模式
                r'【認証コード】[　\s]*：[　\s]*(\d{4,8})',
                
                # 备用模式
                r'【認証コード】[　\s]*[：:][　\s]*(\d{4,8})',
                r'認証コード[　\s]*[：:][　\s]*(\d{4,8})',
            ]
            
            # 使用确定有效的模式提取验证码
            for pattern in code_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # 过滤掉明显不是验证码的结果
                    valid_codes = [code for code in matches if len(code) >= 4 and len(code) <= 8]
                    if valid_codes:
                        verification_code = valid_codes[0]
                        print(f"✅ 找到验证码: {verification_code}")
                        return verification_code
            
            print("❌ 未能提取到验证码")
            return None
            
        except Exception as e:
            print(f"❌ 提取验证码失败: {e}")
            return None

    def get_verification_from_email(self):
        """从邮件中提取验证码"""
        try:
            print("🔍 自动开始搜索XServer验证邮件...")
            if self.search_verification_email():
                verification_code = self.extract_verification_code()
                if verification_code:
                    print(f"🎯 成功提取验证码: {verification_code}")
                    print(f"📋 验证码已复制到剪贴板（如果支持）")
                    # 尝试复制到剪贴板
                    try:
                        import pyperclip
                        pyperclip.copy(verification_code)
                        print("✅ 验证码已复制到剪贴板")
                    except:
                        print("ℹ️ 无法复制到剪贴板，请手动复制验证码")
                    return verification_code
                else:
                    print("⚠️ 未能提取到验证码")
                    return None
            else:
                print("⚠️ 未找到验证邮件")
                return None
                
        except Exception as e:
            print(f"❌ 获取验证码失败: {e}")
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
