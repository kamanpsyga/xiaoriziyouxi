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

# 验证码处理配置
AUTO_VERIFICATION = False  # 手动输入验证码

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
        
        # 验证码配置
        self.auto_verification = AUTO_VERIFICATION
    
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
                    
                    # 手动输入验证码
                    if IS_GITHUB_ACTIONS:
                        print("❌ GitHub Actions环境中无法手动输入验证码")
                        print("💡 请在本地环境中运行此脚本")
                        return False
                    
                    print("🔑 请手动输入验证码...")
                    verification_code = input("请输入收到的验证码: ").strip()
                    
                    if not verification_code:
                        print("❌ 验证码不能为空")
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
    #                       4. 服务器信息获取模块
    # =================================================================
    
    def get_server_time_info(self):
        """获取服务器剩余时间和到期时间信息"""
        try:
            print("🕒 正在获取服务器时间信息...")
            
            # 等待页面完全加载
            time.sleep(3)
            
            # 查找包含时间信息的div标签
            time_info_selectors = [
                "//div[contains(@class, 'limitTxt')]",  # 根据图片中的class名称
                "//div[contains(text(), '残り')]",      # 包含"残り"文本的div
                "//div[contains(text(), '時間')]"       # 包含"時間"文本的div
            ]
            
            remaining_time = None
            expiry_date = None
            
            # 使用集合避免重复处理同一个元素
            processed_elements = set()
            
            for selector in time_info_selectors:
                try:
                    time_elements = self.driver.find_elements(By.XPATH, selector)
                    for element in time_elements:
                        # 使用元素的位置和文本作为唯一标识符
                        element_id = f"{element.location}_{element.text.strip()}"
                        
                        if element_id in processed_elements:
                            continue
                        processed_elements.add(element_id)
                        
                        element_text = element.text.strip()
                        print(f"🔍 找到时间元素: {element_text}")
                        
                        # 从元素文本中分别提取剩余时间和到期时间
                        import re
                        
                        # 提取剩余时间信息 (例如: "残り30時間57分")
                        if not remaining_time and "残り" in element_text and "時間" in element_text:
                            remaining_match = re.search(r'残り\s*\d+\s*時間\s*\d+\s*分', element_text)
                            if remaining_match:
                                remaining_time = remaining_match.group(0)
                                print(f"⏰ 提取剩余时间: {remaining_time}")
                        
                        # 提取到期日期信息 (例如: "(2025-09-24まで)")
                        if not expiry_date and "まで" in element_text:
                            expiry_match = re.search(r'\(?\d{4}-\d{2}-\d{2}\s*まで\)?', element_text)
                            if expiry_match:
                                expiry_date = expiry_match.group(0)
                                print(f"📅 提取到期时间: {expiry_date}")
                        
                        # 如果两个信息都找到了，就不需要继续查找了
                        if remaining_time and expiry_date:
                            break
                            
                except Exception as e:
                    continue
                
                # 如果两个信息都找到了，就退出外层循环
                if remaining_time and expiry_date:
                    break
            
            # 如果上面的方法没找到，尝试更精确的查找
            if not remaining_time or not expiry_date:
                try:
                    # 查找页面源码中的时间信息
                    page_source = self.driver.page_source
                    
                    # 使用正则表达式提取剩余时间
                    import re
                    if not remaining_time:
                        remaining_pattern = r'残り\s*(\d+)\s*時間\s*(\d+)\s*分'
                        remaining_match = re.search(remaining_pattern, page_source)
                        if remaining_match:
                            hours = remaining_match.group(1)
                            minutes = remaining_match.group(2)
                            remaining_time = f"残り{hours}時間{minutes}分"
                            print(f"⏰ 剩余时间(正则): {remaining_time}")
                    
                    # 使用正则表达式提取到期日期
                    if not expiry_date:
                        expiry_pattern = r'\((\d{4}-\d{2}-\d{2})\s*まで\)'
                        expiry_match = re.search(expiry_pattern, page_source)
                        if expiry_match:
                            date = expiry_match.group(1)
                            expiry_date = f"({date}まで)"
                            print(f"📅 到期时间(正则): {expiry_date}")
                            
                except Exception as e:
                    print(f"⚠️ 正则表达式提取失败: {e}")
            
            # 转换时间格式为中文显示
            formatted_remaining = self.format_remaining_time(remaining_time)
            formatted_expiry = self.format_expiry_date(expiry_date)
            
            # 输出最终结果
            print("\n" + "="*50)
            print("📊 XServer GAME 服务器状态信息")
            print("="*50)
            if formatted_remaining:
                print(f"⏰ 剩余时间: {formatted_remaining}")
            else:
                print("⏰ 剩余时间: 无法获取")
                
            if formatted_expiry:
                print(f"📅 到期时间: {formatted_expiry}")
            else:
                print("📅 到期时间: 无法获取")
            print("="*50)
            
            # 点击アップグレード・期限延長按钮
            self.click_upgrade_button()
            
            return formatted_remaining, formatted_expiry
            
        except Exception as e:
            print(f"❌ 获取服务器时间信息失败: {e}")
            return None, None
    
    def format_remaining_time(self, remaining_time):
        """格式化剩余时间为中文显示"""
        if not remaining_time:
            return None
            
        try:
            import re
            # 从日文时间格式中提取数字 (例如: "残り30時間57分" -> "30小时57分")
            pattern = r'残り\s*(\d+)\s*時間\s*(\d+)\s*分'
            match = re.search(pattern, remaining_time)
            
            if match:
                hours = match.group(1)
                minutes = match.group(2)
                return f"{hours}小时{minutes}分"
            else:
                # 如果正则匹配失败，尝试简单替换
                return remaining_time.replace("残り", "").replace("時間", "小时").replace("分", "分")
                
        except Exception as e:
            print(f"⚠️ 格式化剩余时间失败: {e}")
            return remaining_time
    
    def format_expiry_date(self, expiry_date):
        """格式化到期时间为简洁显示"""
        if not expiry_date:
            return None
            
        try:
            import re
            # 从日文格式中提取日期 (例如: "(2025-09-24まで)" -> "2025-09-24")
            pattern = r'\(?(\d{4}-\d{2}-\d{2})'
            match = re.search(pattern, expiry_date)
            
            if match:
                return match.group(1)
            else:
                # 如果正则匹配失败，返回原始值
                return expiry_date.replace("(", "").replace(")", "").replace("まで", "")
                
        except Exception as e:
            print(f"⚠️ 格式化到期时间失败: {e}")
            return expiry_date
    
    def click_upgrade_button(self):
        """点击アップグレード・期限延長按钮"""
        try:
            print("\n🔄 正在查找アップグレード・期限延長按钮...")
            
            # 查找アップグレード・期限延長按钮
            upgrade_selector = "//a[contains(text(), 'アップグレード・期限延長')]"
            
            try:
                upgrade_button = self.driver.find_element(By.XPATH, upgrade_selector)
                print(f"✅ 找到アップグレード・期限延長按钮: {upgrade_selector}")
            except:
                upgrade_button = None
            
            if upgrade_button:
                # 点击按钮
                print("🖱️ 正在点击アップグレード・期限延長按钮...")
                upgrade_button.click()
                print("✅ 已点击アップグレード・期限延長按钮")
                
                # 等待页面跳转
                print("⏰ 等待页面跳转...")
                time.sleep(5)
                
                # 验证跳转结果
                self.verify_upgrade_page()
                
            else:
                print("❌ 未找到アップグレード・期限延長按钮")
                self.take_screenshot("upgrade_button_not_found")
                
        except Exception as e:
            print(f"❌ 点击アップグレード・期限延長按钮时出错: {e}")
            self.take_screenshot("upgrade_button_error")
    
    def verify_upgrade_page(self):
        """验证期限延长页面并检测提示信息"""
        try:
            current_url = self.driver.current_url
            print(f"📍 当前URL: {current_url}")
            
            expected_url = "https://secure.xserver.ne.jp/xmgame/game/freeplan/extend/index"
            
            if expected_url in current_url:
                print("✅ 成功跳转到期限延长页面")
                self.take_screenshot("upgrade_page_loaded")
                
                # 检测期限延长限制提示
                self.check_extension_restriction()
                
            else:
                print(f"❌ 跳转到期限延长页面失败")
                print(f"   预期URL: {expected_url}")
                print(f"   实际URL: {current_url}")
                self.take_screenshot("upgrade_page_failed")
                
        except Exception as e:
            print(f"❌ 验证期限延长页面时出错: {e}")
            self.take_screenshot("upgrade_verify_error")
    
    def check_extension_restriction(self):
        """检测页面是否有期限延长限制提示"""
        try:
            print("🔍 正在检测期限延长限制提示...")
            
            # 使用已验证有效的选择器
            restriction_selector = "//*[contains(text(), '残り契約時間が24時間を切るまで、期限の延長は行えません')]"
            
            restriction_found = False
            restriction_text = ""
            
            try:
                elements = self.driver.find_elements(By.XPATH, restriction_selector)
                
                if elements:
                    print(f"✅ 找到 {len(elements)} 个限制提示元素")
                    
                    for element in elements:
                        element_text = element.text.strip()
                        if "残り契約時間が24時間を切るまで" in element_text:
                            restriction_found = True
                            restriction_text = element_text
                            print(f"✅ 匹配成功！提示信息: {element_text}")
                            break
                else:
                    print("❌ 未找到限制提示元素")
                    
            except Exception as e:
                print(f"❌ 检测限制提示时出错: {e}")
            
            # 输出检测结果
            print("\n" + "="*60)
            print("📋 期限延长检测结果")
            print("="*60)
            
            if restriction_found:
                print("⚠️ 延长状态: 暂时无法延长")
                print(f"📝 提示信息: {restriction_text}")
                print("💡 说明: 需要等待剩余时间少于24小时才能延长期限")
            else:
                print("✅ 延长状态: 可以延长期限")
                print("💡 说明: 当前可以进行期限延长操作")
            
            print("="*60)
            
        except Exception as e:
            print(f"❌ 检测期限延长限制时出错: {e}")
    
    # =================================================================
    #                       5. 登录结果处理模块
    # =================================================================
    
    def handle_login_result(self):
        """处理登录结果"""
        try:
            print("🔍 正在检查登录结果...")
            time.sleep(3)
            
            current_url = self.driver.current_url
            print(f"📍 当前URL: {current_url}")
            
            # 仅通过URL判断是否登录成功
            success_url = "https://secure.xserver.ne.jp/xapanel/xmgame/index"
            if current_url != success_url:
                print("❌ 登录失败！当前URL不是预期的成功页面")
                print(f"   预期URL: {success_url}")
                print(f"   实际URL: {current_url}")
                return False
            
            print("✅ 登录成功！已跳转到XServer GAME管理页面")
            
            # 等待页面加载完成
            print("⏰ 等待页面加载完成...")
            time.sleep(3)
            
            # 查找并点击“ゲーム管理”按钮（只保留有效选择器）
            print("🔍 正在查找ゲーム管理按钮...")
            try:
                game_button = self.driver.find_element(By.XPATH, "//a[contains(text(), 'ゲーム管理')]")
                print("✅ 找到ゲーム管理按钮: //a[contains(text(), 'ゲーム管理')]")
                
                print("🖱️ 正在点击ゲーム管理按钮...")
                game_button.click()
                print("✅ 已点击ゲーム管理按钮")
                
                # 等待页面跳转
                time.sleep(5)
                
                # 验证是否跳转到游戏管理页面
                final_url = self.driver.current_url
                print(f"📍 最终页面URL: {final_url}")
                expected_game_url = "https://secure.xserver.ne.jp/xmgame/game/index"
                if expected_game_url in final_url:
                    print("✅ 成功点击ゲーム管理按钮并跳转到游戏管理页面")
                    self.take_screenshot("game_page_loaded")
                    
                    # 获取服务器时间信息
                    self.get_server_time_info()
                    return True
                else:
                    print("⚠️ 跳转到游戏页面可能失败")
                    print(f"   预期包含: {expected_game_url}")
                    print(f"   实际URL: {final_url}")
                    self.take_screenshot("game_page_redirect_failed")
                    return False
            except Exception as e:
                print(f"❌ 查找或点击ゲーム管理按钮时出错: {e}")
                self.take_screenshot("game_button_error")
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
    print(f"   自动验证: {AUTO_VERIFICATION} (手动输入验证码)")
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