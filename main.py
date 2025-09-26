#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XServer GAME 自动登录和续期脚本
"""

import asyncio
import time
import re
import datetime
from datetime import timezone, timedelta
import os
from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page
from playwright_stealth import stealth_async

# =====================================================================
#                          配置区域
# =====================================================================

# XServer登录信息配置 (支持环境变量)
LOGIN_EMAIL = os.getenv("XSERVER_EMAIL", "")  # 请替换为您的邮箱
LOGIN_PASSWORD = os.getenv("XSERVER_PASSWORD", "")        # 请替换为您的密码

# 网站配置
TARGET_URL = "https://secure.xserver.ne.jp/xapanel/login/xmgame"

# 邮箱验证码获取配置
WEBMAIL_URL = "https://zmkk.edu.kg/login"  # 网页邮箱地址
WEBMAIL_USERNAME = os.getenv("WEBMAIL_USERNAME", "")  # 邮箱登录用户名
WEBMAIL_PASSWORD = os.getenv("WEBMAIL_PASSWORD", "")  # 邮箱密码
TARGET_EMAIL = os.getenv("TARGET_EMAIL", "")  # 要选择的目标邮箱

# 浏览器配置 (GitHub Actions中自动启用无头模式)
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
USE_HEADLESS = IS_GITHUB_ACTIONS or os.getenv("USE_HEADLESS", "false").lower() == "true"
WAIT_TIMEOUT = 10000     # 页面元素等待超时时间（毫秒）
PAGE_LOAD_DELAY = 3      # 页面加载延迟时间（秒）

# 验证码处理配置
AUTO_VERIFICATION = False  # 手动输入验证码

# =====================================================================
#                        XServer 自动登录类
# =====================================================================

class XServerAutoLogin:
    """XServer GAME 自动登录主类 - Playwright版本"""
    
    def __init__(self):
        """
        初始化 XServer GAME 自动登录器
        使用配置区域的设置
        """
        self.browser = None
        self.context = None
        self.page = None
        self.headless = USE_HEADLESS
        self.email = LOGIN_EMAIL
        self.password = LOGIN_PASSWORD
        self.target_url = TARGET_URL
        self.wait_timeout = WAIT_TIMEOUT
        self.page_load_delay = PAGE_LOAD_DELAY
        self.screenshot_count = 0  # 截图计数器
        
        # 验证码配置
        self.auto_verification = AUTO_VERIFICATION
        self.use_auto_verification = False  # 默认为False，由main.py设置为True
        
        # 邮箱验证码获取配置
        self.webmail_url = WEBMAIL_URL
        self.webmail_username = WEBMAIL_USERNAME
        self.webmail_password = WEBMAIL_PASSWORD
        self.target_email = TARGET_EMAIL
        
        # 标签页管理 - 使用编号系统
        self.tab_1_xserver = None    # 标签页#1 - XServer登录页面
        self.tab_2_backup = None     # 标签页#2 - 备用标签页（邮箱登录用）
        self.current_active_tab = 1  # 当前活跃标签页编号
        
        # 续期状态跟踪
        self.old_expiry_time = None      # 原到期时间
        self.new_expiry_time = None      # 新到期时间
        self.renewal_status = "Unknown"  # 续期状态: Success/Unexpired/Failed/Unknown
    
    def get_active_page(self):
        """根据当前活跃标签页编号获取页面"""
        if self.current_active_tab == 1:
            return self.tab_1_xserver if self.tab_1_xserver else self.page
        elif self.current_active_tab == 2:
            return self.tab_2_backup
        else:
            return self.page  # 默认返回主页面
    
    def switch_to_tab(self, tab_number):
        """切换到指定编号的标签页"""
        print(f"🔄 请求切换到标签页#{tab_number}...")
        
        if tab_number == 1 and self.tab_1_xserver:
            old_tab = self.current_active_tab
            self.current_active_tab = 1
            print(f"✅ 已切换: 标签页#{old_tab} → 标签页#{tab_number} (XServer登录页面)")
            return True
        elif tab_number == 2 and self.tab_2_backup:
            old_tab = self.current_active_tab
            self.current_active_tab = 2
            print(f"✅ 已切换: 标签页#{old_tab} → 标签页#{tab_number} (备用标签页)")
            return True
        else:
            print(f"❌ 标签页#{tab_number} 不存在或未初始化")
            return False
    
    # =================================================================
    #                       1. 浏览器管理模块
    # =================================================================
        
    async def setup_browser(self):
        """设置并启动 Playwright 浏览器"""
        try:
            playwright = await async_playwright().start()
            
            # 配置浏览器选项
            browser_args = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-notifications',
                '--window-size=1920,1080',
                '--lang=ja-JP',
                '--accept-lang=ja-JP,ja,en-US,en'
            ]
            
            # 启动浏览器
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # 创建浏览器上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='ja-JP',
                timezone_id='Asia/Tokyo',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # 创建页面
            self.page = await self.context.new_page()
            
            # 应用stealth插件
            await stealth_async(self.page)
            print("✅ Stealth 插件已应用")
            
            print("✅ Playwright 浏览器初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ Playwright 浏览器初始化失败: {e}")
            return False
    
    async def take_screenshot(self, step_name=""):
        """截图功能 - 用于可视化调试"""
        try:
            active_page = self.get_active_page()
            if active_page:
                self.screenshot_count += 1
                # 使用北京时间（UTC+8）
                beijing_time = datetime.datetime.now(timezone(timedelta(hours=8)))
                timestamp = beijing_time.strftime("%H%M%S")
                filename = f"step_{self.screenshot_count:02d}_{timestamp}_{step_name}.png"
                
                # 确保文件名安全
                filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                
                await active_page.screenshot(path=filename, full_page=True)
                print(f"📸 截图已保存: {filename} (标签页#{self.current_active_tab})")
                
        except Exception as e:
            print(f"⚠️ 截图失败: {e}")
    
    def validate_config(self):
        """验证配置信息"""
        if not self.email or not self.password:
            print("❌ 邮箱或密码未设置！")
            return False
        
        print("✅ 配置信息验证通过")
        return True
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            print("🧹 浏览器已关闭")
        except Exception as e:
            print(f"⚠️ 清理资源时出错: {e}")
    
    # =================================================================
    #                       2. 页面导航模块
    # =================================================================
    
    async def navigate_to_login(self):
        """导航到登录页面"""
        try:
            print(f"🌐 正在访问: {self.target_url}")
            await self.page.goto(self.target_url, wait_until='load')
            
            # 等待页面加载
            await self.page.wait_for_selector("body", timeout=self.wait_timeout)
            
            print("✅ 页面加载成功")
            await self.take_screenshot("login_page_loaded")
            return True
            
        except Exception as e:
            print(f"❌ 导航失败: {e}")
            return False
    
    async def prepare_new_tab(self):
        """预先创建新标签页（用于可能的邮箱验证）"""
        try:
            print("🆕 预先创建标签页系统...")
            
            # 标签页#1：当前XServer登录页面
            self.tab_1_xserver = self.page
            print("📋 标签页#1：XServer登录页面 ✅")
            
            # 创建标签页#2：备用标签页
            print("🆕 正在创建标签页#2：备用标签页...")
            self.tab_2_backup = await self.context.new_page()
            
            # 应用stealth插件到新页面
            await stealth_async(self.tab_2_backup)
            print("📋 标签页#2：备用标签页 ✅")
            
            # 确保当前活跃标签页是#1（XServer页面）
            self.current_active_tab = 1
            print("🎯 当前活跃标签页：#1 (XServer登录页面)")
            
            # 验证标签页#1页面状态
            current_url = self.tab_1_xserver.url
            print(f"📍 标签页#1 URL: {current_url}")
            
            if "xmgame" in current_url:
                print("✅ 标签页#1 XServer页面确认正常")
            else:
                print("⚠️ 标签页#1 URL异常，但继续执行")
            
            print("🎉 标签页系统初始化完成！")
            print("   📋 标签页#1：XServer登录页面 (当前活跃)")
            print("   📋 标签页#2：备用标签页 (待用)")
            
            return True
            
        except Exception as e:
            print(f"❌ 标签页系统初始化失败: {e}")
            return False
    
    # =================================================================
    #                       3. 登录表单处理模块
    # =================================================================
    
    async def find_login_form(self):
        """查找登录表单元素"""
        try:
            print("🔍 正在查找登录表单...")
            active_page = self.get_active_page()
            
            # 等待页面加载完成
            await asyncio.sleep(self.page_load_delay)
            
            # 查找邮箱输入框
            email_selector = "input[name='memberid']"
            await active_page.wait_for_selector(email_selector, timeout=self.wait_timeout)
            print("✅ 找到邮箱输入框: input[name='memberid']")
            
            # 查找密码输入框
            password_selector = "input[name='user_password']"
            await active_page.wait_for_selector(password_selector, timeout=self.wait_timeout)
            print("✅ 找到密码输入框: input[name='user_password']")
            
            # 查找登录按钮
            login_button_selector = "input[value='ログインする']"
            await active_page.wait_for_selector(login_button_selector, timeout=self.wait_timeout)
            print("✅ 找到登录按钮: input[value='ログインする']")
            
            return email_selector, password_selector, login_button_selector
            
        except Exception as e:
            print(f"❌ 查找登录表单时出错: {e}")
            return None, None, None
    
    async def human_type(self, selector, text):
        """模拟人类输入行为"""
        active_page = self.get_active_page()
        for char in text:
            await active_page.type(selector, char, delay=100)  # 100ms delay between characters
            await asyncio.sleep(0.05)  # Additional small delay
    
    async def perform_login(self):
        """执行登录操作"""
        try:
            print(f"🎯 当前操作标签页：#{self.current_active_tab}")
            
            # 查找登录表单元素
            email_selector, password_selector, login_button_selector = await self.find_login_form()
            
            if not email_selector or not password_selector:
                return False
            
            print("📝 正在填写登录信息...")
            active_page = self.get_active_page()
            
            # 模拟人类行为：慢速输入邮箱
            await active_page.fill(email_selector, "")  # 清空
            await self.human_type(email_selector, self.email)
            print("✅ 邮箱已填写")
            
            # 等待一下，模拟人类思考时间
            await asyncio.sleep(2)
            
            # 模拟人类行为：慢速输入密码
            await active_page.fill(password_selector, "")  # 清空
            await self.human_type(password_selector, self.password)
            print("✅ 密码已填写")
            
            # 等待一下，模拟人类操作
            await asyncio.sleep(2)
            
            # 提交表单
            if login_button_selector:
                print("🖱️ 点击登录按钮...")
                await active_page.click(login_button_selector)
            else:
                print("⌨️ 使用回车键提交...")
                await active_page.press(password_selector, "Enter")
            
            print("✅ 登录表单已提交")
            
            # 等待页面响应
            await asyncio.sleep(5)
            return True
            
        except Exception as e:
            print(f"❌ 登录操作失败: {e}")
            return False
    
    # =================================================================
    #                       4. 验证码处理模块
    # =================================================================
    
    async def handle_verification_page(self):
        """处理验证页面"""
        try:
            print("🔍 检查是否需要验证...")
            print(f"🎯 当前操作标签页：#{self.current_active_tab}")
            await self.take_screenshot("checking_verification_page")
            
            # 等待页面稳定
            await asyncio.sleep(3)
            
            active_page = self.get_active_page()
            current_url = active_page.url
            print(f"📍 当前URL: {current_url}")
            
            # 检查是否跳转到验证页面
            if "loginauth/index" in current_url:
                print("🔐 检测到XServer新环境验证页面！")
                print("⚠️ 这是XServer的安全机制，检测到新环境登录")
                
                # 查找发送验证码按钮
                send_code_selectors = [
                    "input[value*='送信']",
                    "input[value*='認証コードを送信']",
                    "button:has-text('送信')",
                    ".button:has-text('送信')"
                ]
                
                for selector in send_code_selectors:
                    try:
                        await active_page.wait_for_selector(selector, timeout=5000)
                        print("✅ 找到发送验证码按钮")
                        print("📧 已点击发送验证码按钮，验证码正在发送到您的邮箱")
                        await active_page.click(selector)
                        break
                    except:
                        continue
                
                # 等待跳转到验证码输入页面
                await asyncio.sleep(5)
                return await self.handle_code_input_page()
            
            return True
            
        except Exception as e:
            print(f"❌ 处理验证页面时出错: {e}")
            return False
    
    async def handle_code_input_page(self):
        """处理验证码输入页面"""
        try:
            print("🔍 检查是否跳转到验证码输入页面...")
            print(f"🎯 当前操作标签页：#{self.current_active_tab}")
            active_page = self.get_active_page()
            current_url = active_page.url
            print(f"📍 当前URL: {current_url}")
            
            if "loginauth/smssend" in current_url:
                print("✅ 成功跳转到验证码输入页面！")
                print("📧 请检查您的邮箱获取验证码")
                
                # 查找验证码输入框
                print("🔍 正在查找验证码输入框...")
                code_input_selector = "input[id='auth_code'][name='auth_code']"
                
                try:
                    await active_page.wait_for_selector(code_input_selector, timeout=self.wait_timeout)
                    print("✅ 找到验证码输入框")
                    
                    verification_code = None
                    
                    # 检查是否使用自动验证码模式（GitHub Actions或use_auto_verification）
                    if IS_GITHUB_ACTIONS or self.use_auto_verification:
                        if IS_GITHUB_ACTIONS:
                            print("🤖 GitHub Actions环境，自动获取验证码...")
                        else:
                            print("🤖 本地自动模式，自动获取验证码...")
                        
                        # 自动获取验证码
                        verification_code = await self.get_verification_code_from_email()
                        
                        if verification_code:
                            # 输入验证码
                            await active_page.fill(code_input_selector, "")
                            await self.human_type(code_input_selector, verification_code)
                            print("✅ 验证码已输入")
                            
                            # 等待输入完成
                            await asyncio.sleep(2)
                            
                            # 查找并点击登录按钮
                            print("🔍 正在查找ログイン按钮...")
                            login_submit_selector = "input[type='submit'][value='ログイン']"
                            await active_page.wait_for_selector(login_submit_selector, timeout=self.wait_timeout)
                            print("✅ 找到ログイン按钮")
                            
                            # 等待按钮可点击
                            await asyncio.sleep(1)
                            await active_page.click(login_submit_selector)
                            print("✅ 验证码已提交")
                            
                            # 等待验证结果
                            await asyncio.sleep(8)
                            return True
                        else:
                            print("❌ 自动获取验证码失败")
                            return False
                    
                    print("🔑 请手动输入验证码...")
                    verification_code = input("请输入收到的验证码: ").strip()
                    
                    if verification_code:
                        # 输入验证码
                        await active_page.fill(code_input_selector, "")
                        await self.human_type(code_input_selector, verification_code)
                        print("✅ 验证码已输入")
                        
                        # 等待输入完成
                        await asyncio.sleep(2)
                        
                        # 查找并点击登录按钮
                        print("🔍 正在查找ログイン按钮...")
                        login_submit_selector = "input[type='submit'][value='ログイン']"
                        await active_page.wait_for_selector(login_submit_selector, timeout=self.wait_timeout)
                        print("✅ 找到ログイン按钮")
                        
                        # 等待按钮可点击
                        await asyncio.sleep(1)
                        await active_page.click(login_submit_selector)
                        print("✅ 验证码已提交")
                        
                        # 等待验证结果
                        await asyncio.sleep(8)
                        return True
                    else:
                        print("❌ 验证码不能为空")
                        return False
                        
                except Exception as e:
                    print(f"❌ 未找到验证码输入框: {e}")
                    return False
            else:
                print("⚠️ 未检测到验证码输入页面，可能已直接登录成功")
                return True
                
        except Exception as e:
            print(f"❌ 处理验证码输入页面时出错: {e}")
            return False
    
    async def input_verification_code_externally(self, verification_code):
        """从外部输入验证码（用于main.py调用）"""
        try:
            print(f"🔑 正在输入外部获取的验证码: {verification_code}")
            print(f"🎯 当前操作标签页：#{self.current_active_tab}")
            
            # 确保在标签页#1上操作
            if self.current_active_tab != 1:
                print(f"⚠️ 当前不在标签页#1，自动切换...")
                self.switch_to_tab(1)
            
            # 等待页面稳定
            await asyncio.sleep(2)
            
            active_page = self.get_active_page()
            
            # 查找验证码输入框
            code_input_selector = "input[id='auth_code'][name='auth_code']"
            
            # 清空并输入验证码
            await active_page.fill(code_input_selector, "")
            await asyncio.sleep(1)  # 等待清空完成
            await self.human_type(code_input_selector, verification_code)
            print("✅ 验证码已输入")
            
            # 等待输入完成
            await asyncio.sleep(2)
            
            # 查找并点击登录按钮
            print("🔍 正在查找ログイン按钮...")
            login_submit_selector = "input[type='submit'][value='ログイン']"
            await active_page.wait_for_selector(login_submit_selector, timeout=self.wait_timeout)
            print("✅ 找到ログイン按钮")
            
            # 等待按钮可点击
            await asyncio.sleep(1)
            await active_page.click(login_submit_selector)
            print("✅ 验证码已提交")
            
            # 等待验证结果
            await asyncio.sleep(8)  # 增加等待时间
            return True
            
        except Exception as e:
            print(f"❌ 输入验证码失败: {e}")
            # 尝试截图保存现场
            try:
                await self.take_screenshot("verification_input_failed")
            except:
                pass
            return False
    
    # =================================================================
    #                       5. 邮箱验证码获取模块
    # =================================================================
    
    async def perform_webmail_login_in_tab2(self):
        """在标签页#2中执行邮箱登录"""
        try:
            print("📧 开始在标签页#2进行邮箱登录...")
            
            # 确保切换到标签页#2
            if not self.switch_to_tab(2):
                return False
            
            active_page = self.get_active_page()
            
            # 导航到邮箱登录页面
            print(f"🌐 正在访问邮箱: {self.webmail_url}")
            await active_page.goto(self.webmail_url, wait_until='load')
            
            # 等待页面加载
            await active_page.wait_for_selector("body", timeout=self.wait_timeout)
            print("✅ 邮箱页面加载成功")
            
            # 等待页面完全加载
            print("⏰ 等待页面完全加载...")
            await asyncio.sleep(5)
            
            # 打印页面信息用于调试
            print(f"📍 当前URL: {active_page.url}")
            print(f"📄 页面标题: {await active_page.title()}")
            
            # 检查页面是否包含预期元素
            page_content = await active_page.content()
            if "邮箱" in page_content or "email" in page_content.lower():
                print("✅ 页面包含邮箱相关内容")
            else:
                print("⚠️ 页面可能未完全加载或结构不同")
            
            # 登录部分已确定，保持简化（完全按照code.py的配置）
            email_selector = "input[placeholder='邮箱']"
            password_selector = "input[placeholder='密码']"
            login_selector = "button.el-button.el-button--primary.btn"
            
            # 查找邮箱输入框
            try:
                await active_page.wait_for_selector(email_selector, timeout=self.wait_timeout)
                print(f"✅ 找到邮箱输入框: {email_selector}")
            except:
                print("❌ 未找到邮箱输入框")
                return False
            
            # 查找密码输入框
            try:
                await active_page.wait_for_selector(password_selector, timeout=self.wait_timeout)
                print(f"✅ 找到密码输入框: {password_selector}")
            except:
                print("❌ 未找到密码输入框")
                return False
            
            # 查找登录按钮
            try:
                await active_page.wait_for_selector(login_selector, timeout=self.wait_timeout)
                print(f"✅ 找到登录按钮: {login_selector}")
            except:
                print("❌ 未找到登录按钮")
                return False
            
            # 执行登录操作（完全按照code.py的逻辑）
            print("📝 正在执行邮箱登录...")
            
            # 填写邮箱地址
            print("📧 正在填写邮箱地址...")
            await active_page.fill(email_selector, "")  # 清空
            await self.human_type_in_tab(active_page, email_selector, self.webmail_username)
            print("✅ 邮箱已填写")
            
            # 等待一下
            await asyncio.sleep(2)
            
            # 填写密码
            print("🔐 正在填写密码...")
            await active_page.fill(password_selector, "")  # 清空
            await self.human_type_in_tab(active_page, password_selector, self.webmail_password)
            print("✅ 密码已填写")
            
            # 等待一下
            await asyncio.sleep(2)
            
            # 点击登录按钮
            print("🖱️ 点击登录按钮...")
            await active_page.click(login_selector)
            print("✅ 登录表单已提交")
            
            # 等待登录响应
            await asyncio.sleep(5)
            
            # 检查登录结果（完全按照code.py的逻辑）
            print("🔍 正在检查登录结果...")
            
            # 等待页面响应
            await asyncio.sleep(3)
            
            current_url = active_page.url
            page_title = await active_page.title()
            
            print(f"📍 当前URL: {current_url}")
            print(f"📄 页面标题: {page_title}")
            
            # 检查是否成功跳转到邮箱页面
            if "email" in current_url:
                print("✅ 成功跳转到邮箱页面，登录成功！")
                return True
            else:
                print("❌ 邮箱登录失败")
                return False
                
        except Exception as e:
            print(f"❌ 邮箱登录过程出错: {e}")
            return False
    
    async def human_type_in_tab(self, page, selector, text):
        """在指定标签页中模拟人类输入行为"""
        for char in text:
            await page.type(selector, char, delay=100)
            await asyncio.sleep(0.05)
    
    async def select_target_mailbox_in_tab2(self):
        """在标签页#2中选择目标邮箱"""
        try:
            print("📧 正在选择目标邮箱...")
            print(f"🔐 登录邮箱: {self.webmail_username}")
            print(f"🎯 目标邮箱: {self.target_email}")
            
            active_page = self.get_active_page()
            
            # 等待邮箱列表加载
            await asyncio.sleep(3)
            
            # 基于HTML结构，使用更精确的选择器
            target_selectors = [
                f"div.account:has-text('{self.target_email}')",  # 基于class="account"的div
                f".account:has-text('{self.target_email}')",  # class="account"的元素
                f"div:has-text('{self.target_email}')",  # 任何包含目标邮箱的div
                f":has-text('{self.target_email}')",  # 任何包含目标邮箱的元素
                f"[data-v]:has-text('{self.target_email}')"  # 带data-v属性的元素
            ]
            
            for i, selector in enumerate(target_selectors):
                try:
                    print(f"🔍 尝试选择器 {i+1}: {selector}")
                    
                    # 等待元素出现
                    elements = await active_page.locator(selector).all()
                    if elements:
                        print(f"   ✅ 找到 {len(elements)} 个匹配元素")
                        
                        # 点击第一个匹配的元素
                        await elements[0].click()
                        print(f"✅ 找到目标邮箱: {self.target_email}")
                        print(f"✅ 已选择 {self.target_email} 邮箱")
                        return True
                    else:
                        print(f"   ❌ 未找到匹配元素")
                    
                except Exception as selector_error:
                    print(f"   ❌ 选择器 {i+1} 失败: {selector_error}")
                    continue
            
            print("❌ 所有选择器都未找到目标邮箱")
            
            # 调试：显示页面上所有可能的邮箱元素（完全按照code.py）
            try:
                print("🔍 调试：页面上的邮箱相关元素...")
                elements = await active_page.locator("div.account, .account").all()
                print(f"   找到 {len(elements)} 个account元素:")
                for i, element in enumerate(elements):
                    try:
                        element_text = await element.text_content()
                        print(f"   元素{i+1}: '{element_text.strip()}'")
                    except:
                        print(f"   元素{i+1}: [无法获取文本]")
            except Exception as debug_error:
                print(f"   调试信息获取失败: {debug_error}")
            
            return False
                
        except Exception as e:
            print(f"❌ 选择目标邮箱失败: {e}")
            return False
    
    async def scroll_to_load_emails_in_tab2(self):
        """在标签页#2中滚动页面加载所有邮件"""
        try:
            print("📜 正在滚动页面加载所有邮件...")
            
            active_page = self.get_active_page()
            
            # 多次滚动以确保加载所有邮件
            for i in range(5):
                await active_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
                print(f"   滚动第 {i+1} 次")
            
            # 滚动回顶部
            await active_page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(2)
            
            print("✅ 页面滚动完成，邮件列表已加载")
            return True
            
        except Exception as e:
            print(f"❌ 滚动加载邮件失败: {e}")
            return False
    
    async def search_verification_email_in_tab2(self):
        """在标签页#2中搜索XServer验证码邮件"""
        try:
            print("🔍 正在搜索XServer验证码邮件...")
            
            active_page = self.get_active_page()
            
            # 滚动加载邮件
            await self.scroll_to_load_emails_in_tab2()
            
            # 查找XServer邮件
            xserver_selectors = [
                "text=/【XServerアカウント】ログイン用認証コードのお知らせ/",
                ":has-text('XServerアカウント')",
                ":has-text('認証コード')"
            ]
            
            xserver_emails = []
            
            for selector in xserver_selectors:
                try:
                    elements = await active_page.locator(selector).all()
                    if elements:
                        print(f"✅ 使用选择器找到 {len(elements)} 封邮件: {selector}")
                        xserver_emails = elements
                        break
                except:
                    continue
            
            if not xserver_emails:
                print("❌ 未找到XServer验证码邮件")
                return False
            
            print(f"📊 统计结果:")
            print(f"   🎯 总共找到: {len(xserver_emails)} 封XServerアカウント邮件")
            print(f"   ✅ 有效选择器: 1 个")
            
            # 显示邮件列表（完全按照code.py）
            print(f"   📧 邮件列表:")
            for i, email in enumerate(xserver_emails[:10]):  # 只显示前10封
                try:
                    email_text = await email.text_content()
                    email_preview = email_text[:80] + "..." if len(email_text) > 80 else email_text
                    print(f"      {i+1}. ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ {email_preview}")
                except:
                    print(f"      {i+1}. [无法获取邮件预览]")
            
            if len(xserver_emails) > 10:
                print(f"      ... 还有 {len(xserver_emails) - 10} 封邮件")
            
            # 点击第一封（最新的）邮件
            print("🎯 正在打开第一封（最新的）XServerアカウント邮件...")
            try:
                await xserver_emails[0].click()
                await asyncio.sleep(3)
                print("✅ 已成功打开最新的XServerアカウント邮件")
                return True
            except Exception as e:
                print(f"❌ 点击邮件失败: {e}")
                return False
                
        except Exception as e:
            print(f"❌ 搜索验证码邮件失败: {e}")
            return False
    
    async def extract_verification_code_in_tab2(self):
        """在标签页#2中从邮件内容提取验证码"""
        try:
            print("🔍 正在提取验证码...")
            
            active_page = self.get_active_page()
            
            # 获取页面内容
            page_content = await active_page.content()
            
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
                matches = re.findall(pattern, page_content, re.IGNORECASE | re.MULTILINE)
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
    
    async def get_verification_code_from_email(self):
        """完整的邮箱验证码获取流程"""
        try:
            print("📧 开始邮箱验证码获取流程...")
            
            # 等待验证码邮件发送
            print("⏰ 等待验证码邮件发送...")
            await asyncio.sleep(30)
            
            # 步骤1：在标签页#2执行邮箱登录
            if not await self.perform_webmail_login_in_tab2():
                return None
            
            # 步骤2：选择目标邮箱
            if not await self.select_target_mailbox_in_tab2():
                return None
            
            # 步骤3：搜索验证码邮件
            if not await self.search_verification_email_in_tab2():
                return None
            
            # 步骤4：提取验证码
            verification_code = await self.extract_verification_code_in_tab2()
            if verification_code:
                print(f"🎉 成功获取验证码: {verification_code}")
                return verification_code
            else:
                print("❌ 验证码获取失败")
                return None
                
        except Exception as e:
            print(f"❌ 邮箱验证码获取流程失败: {e}")
            return None
        
        finally:
            # 切换回标签页#1
            print("🔙 切换回标签页#1...")
            self.switch_to_tab(1)
    
    # =================================================================
    #                       6. 登录结果处理模块
    # =================================================================
    
    async def handle_login_result(self):
        """处理登录结果"""
        try:
            print("🔍 正在检查登录结果...")
            print(f"🎯 当前操作标签页：#{self.current_active_tab}")
            
            # 确保在标签页#1上操作
            if self.current_active_tab != 1:
                print(f"⚠️ 当前不在标签页#1，自动切换...")
                self.switch_to_tab(1)
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            active_page = self.get_active_page()
            current_url = active_page.url
            print(f"📍 当前URL: {current_url}")
            
            # 简单直接：只判断是否跳转到成功页面
            success_url = "https://secure.xserver.ne.jp/xapanel/xmgame/index"
            
            if current_url == success_url:
                print("✅ 登录成功！已跳转到XServer GAME管理页面")
                
                # 等待页面加载完成
                print("⏰ 等待页面加载完成...")
                await asyncio.sleep(3)
                
                # 查找并点击"ゲーム管理"按钮
                print("🔍 正在查找ゲーム管理按钮...")
                try:
                    game_button_selector = "a:has-text('ゲーム管理')"
                    await active_page.wait_for_selector(game_button_selector, timeout=self.wait_timeout)
                    print("✅ 找到ゲーム管理按钮")
                    
                    # 点击ゲーム管理按钮
                    print("🖱️ 正在点击ゲーム管理按钮...")
                    await active_page.click(game_button_selector)
                    print("✅ 已点击ゲーム管理按钮")
                    
                    # 等待页面跳转
                    await asyncio.sleep(5)
                    
                    # 验证是否跳转到游戏管理页面
                    final_url = active_page.url
                    print(f"📍 最终页面URL: {final_url}")
                    
                    expected_game_url = "https://secure.xserver.ne.jp/xmgame/game/index"
                    if expected_game_url in final_url:
                        print("✅ 成功点击ゲーム管理按钮并跳转到游戏管理页面")
                        await self.take_screenshot("game_page_loaded")
                        
                        # 获取服务器时间信息
                        await self.get_server_time_info()
                    else:
                        print(f"⚠️ 跳转到游戏页面可能失败")
                        print(f"   预期包含: {expected_game_url}")
                        print(f"   实际URL: {final_url}")
                        await self.take_screenshot("game_page_redirect_failed")
                        
                except Exception as e:
                    print(f"❌ 查找或点击ゲーム管理按钮时出错: {e}")
                    await self.take_screenshot("game_button_error")
                
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
    #                    6A. 服务器信息获取模块
    # =================================================================
    
    async def get_server_time_info(self):
        """获取服务器时间信息"""
        try:
            print("🕒 正在获取服务器时间信息...")
            print(f"🎯 当前操作标签页：#{self.current_active_tab}")
            
            # 确保在标签页#1上操作
            if self.current_active_tab != 1:
                print(f"⚠️ 当前不在标签页#1，自动切换...")
                self.switch_to_tab(1)
            
            # 等待页面加载完成
            await asyncio.sleep(3)
            
            # 使用已验证有效的选择器
            try:
                active_page = self.get_active_page()
                elements = await active_page.locator("text=/残り\\d+時間\\d+分/").all()
                
                for element in elements:
                    element_text = await element.text_content()
                    element_text = element_text.strip() if element_text else ""
                    
                    # 只处理包含时间信息且文本不太长的元素
                    if element_text and len(element_text) < 200 and "残り" in element_text and "時間" in element_text:
                        print(f"✅ 找到时间元素: {element_text}")
                        
                        # 提取剩余时间
                        remaining_match = re.search(r'残り(\d+時間\d+分)', element_text)
                        if remaining_match:
                            remaining_raw = remaining_match.group(1)
                            remaining_formatted = self.format_remaining_time(remaining_raw)
                            print(f"⏰ 剩余时间: {remaining_formatted}")
                        
                        # 提取到期时间
                        expiry_match = re.search(r'\((\d{4}-\d{2}-\d{2})まで\)', element_text)
                        if expiry_match:
                            expiry_raw = expiry_match.group(1)
                            expiry_formatted = self.format_expiry_date(expiry_raw)
                            print(f"📅 到期时间: {expiry_formatted}")
                            # 记录原到期时间
                            self.old_expiry_time = expiry_formatted
                        
                        break
                        
            except Exception as e:
                print(f"❌ 获取时间信息时出错: {e}")
            
            # 点击升级按钮
            await self.click_upgrade_button()
            
        except Exception as e:
            print(f"❌ 获取服务器时间信息失败: {e}")
    
    def format_remaining_time(self, time_str):
        """格式化剩余时间"""
        # 移除"残り"前缀，只保留时间部分
        return time_str  # 例如: "30時間57分"
    
    def format_expiry_date(self, date_str):
        """格式化到期时间"""
        # 直接返回日期，移除括号和"まで"
        return date_str  # 例如: "2025-09-24"
    
    # =================================================================
    #                    6B. 续期页面导航模块
    # =================================================================
    
    async def click_upgrade_button(self):
        """点击升级延长按钮"""
        try:
            print("🔄 正在查找アップグレード・期限延長按钮...")
            
            active_page = self.get_active_page()
            upgrade_selector = "a:has-text('アップグレード・期限延長')"
            await active_page.wait_for_selector(upgrade_selector, timeout=self.wait_timeout)
            print("✅ 找到アップグレード・期限延長按钮")
            
            # 点击按钮
            await active_page.click(upgrade_selector)
            print("✅ 已点击アップグレード・期限延長按钮")
            
            # 等待页面跳转
            await asyncio.sleep(5)
            
            # 验证URL和检查限制信息
            await self.verify_upgrade_page()
            
        except Exception as e:
            print(f"❌ 点击升级按钮失败: {e}")
    
    async def verify_upgrade_page(self):
        """验证升级页面"""
        try:
            active_page = self.get_active_page()
            current_url = active_page.url
            expected_url = "https://secure.xserver.ne.jp/xmgame/game/freeplan/extend/index"
            
            print(f"📍 升级页面URL: {current_url}")
            
            if expected_url in current_url:
                print("✅ 成功跳转到升级页面")
                
                # 检查延长限制信息
                await self.check_extension_restriction()
            else:
                print(f"❌ 升级页面跳转失败")
                print(f"   预期URL: {expected_url}")
                print(f"   实际URL: {current_url}")
                
        except Exception as e:
            print(f"❌ 验证升级页面失败: {e}")
    
    async def check_extension_restriction(self):
        """检查期限延长限制信息"""
        try:
            print("🔍 正在检测期限延长限制提示...")
            
            # 查找限制信息
            restriction_selector = "text=/残り契約時間が24時間を切るまで、期限の延長は行えません/"
            
            try:
                active_page = self.get_active_page()
                element = await active_page.wait_for_selector(restriction_selector, timeout=5000)
                restriction_text = await element.text_content()
                print(f"✅ 找到期限延长限制信息")
                print(f"📝 限制信息: {restriction_text}")
                # 设置状态为未到期
                self.renewal_status = "Unexpired"
                return True  # 有限制，不能续期
                
            except Exception:
                print("ℹ️ 未找到期限延长限制信息，可以进行延长操作")
                # 没有限制信息，执行续期操作
                await self.perform_extension_operation()
                return False  # 无限制，可以续期
                
        except Exception as e:
            print(f"❌ 检测期限延长限制失败: {e}")
            return True  # 出错时默认认为有限制
    
    # =================================================================
    #                    6C. 续期操作执行模块
    # =================================================================
    
    async def perform_extension_operation(self):
        """执行期限延长操作"""
        try:
            print("🔄 开始执行期限延长操作...")
            
            # 查找"期限を延長する"按钮
            await self.click_extension_button()
            
        except Exception as e:
            print(f"❌ 执行期限延长操作失败: {e}")
    
    async def click_extension_button(self):
        """点击期限延长按钮"""
        try:
            print("🔍 正在查找'期限を延長する'按钮...")
            
            active_page = self.get_active_page()
            
            # 使用有效的选择器
            extension_selector = "a:has-text('期限を延長する')"
            
            # 等待并点击按钮
            await active_page.wait_for_selector(extension_selector, timeout=self.wait_timeout)
            print("✅ 找到'期限を延長する'按钮")
            
            # 点击按钮
            await active_page.click(extension_selector)
            print("✅ 已点击'期限を延長する'按钮")
            
            # 等待页面跳转
            print("⏰ 等待页面跳转...")
            await asyncio.sleep(5)
            
            # 验证是否跳转到input页面
            await self.verify_extension_input_page()
            return True
            
        except Exception as e:
            print(f"❌ 点击期限延长按钮失败: {e}")
            return False
    
    async def verify_extension_input_page(self):
        """验证是否成功跳转到期限延长输入页面"""
        try:
            active_page = self.get_active_page()
            current_url = active_page.url
            expected_url = "https://secure.xserver.ne.jp/xmgame/game/freeplan/extend/input"
            
            print(f"📍 当前页面URL: {current_url}")
            
            if expected_url in current_url:
                print("🎉 成功跳转到期限延长输入页面！")
                await self.take_screenshot("extension_input_page")
                
                # 继续执行确认操作
                await self.click_confirmation_button()
                return True
            else:
                print(f"❌ 页面跳转失败")
                print(f"   预期URL: {expected_url}")
                print(f"   实际URL: {current_url}")
                return False
                
        except Exception as e:
            print(f"❌ 验证期限延长输入页面失败: {e}")
            return False
    
    async def click_confirmation_button(self):
        """点击確認画面に進む按钮"""
        try:
            print("🔍 正在查找'確認画面に進む'按钮...")
            
            active_page = self.get_active_page()
            
            # 使用button元素的选择器
            confirmation_selector = "button[type='submit']:has-text('確認画面に進む')"
            
            # 等待并点击按钮
            await active_page.wait_for_selector(confirmation_selector, timeout=self.wait_timeout)
            print("✅ 找到'確認画面に進む'按钮")
            
            # 点击按钮
            await active_page.click(confirmation_selector)
            print("✅ 已点击'確認画面に進む'按钮")
            
            # 等待页面跳转
            print("⏰ 等待页面跳转...")
            await asyncio.sleep(5)
            
            # 验证是否跳转到conf页面
            await self.verify_extension_conf_page()
            return True
            
        except Exception as e:
            print(f"❌ 点击確認画面に進む按钮失败: {e}")
            return False
    
    async def verify_extension_conf_page(self):
        """验证是否成功跳转到期限延长确认页面"""
        try:
            active_page = self.get_active_page()
            current_url = active_page.url
            expected_url = "https://secure.xserver.ne.jp/xmgame/game/freeplan/extend/conf"
            
            print(f"📍 当前页面URL: {current_url}")
            
            if expected_url in current_url:
                print("🎉 成功跳转到期限延长确认页面！")
                await self.take_screenshot("extension_conf_page")
                
                # 记录续期后的时间信息
                await self.record_extension_time()
                
                # 查找期限延长按钮
                await self.find_final_extension_button()
                
                return True
            else:
                print(f"❌ 页面跳转失败")
                print(f"   预期URL: {expected_url}")
                print(f"   实际URL: {current_url}")
                return False
                
        except Exception as e:
            print(f"❌ 验证期限延长确认页面失败: {e}")
            return False
    
    async def record_extension_time(self):
        """记录续期后的时间信息"""
        try:
            print("📅 正在获取续期后的时间信息...")
            
            active_page = self.get_active_page()
            
            # 使用有效的选择器
            time_selector = "tr:has(th:has-text('延長後の期限'))"
            
            # 等待并获取时间信息
            time_element = await active_page.wait_for_selector(time_selector, timeout=self.wait_timeout)
            print("✅ 找到续期后时间信息")
            
            # 获取整行，然后提取td内容
            td_element = await time_element.query_selector("td")
            if td_element:
                extension_time = await td_element.text_content()
                extension_time = extension_time.strip()
                print(f"📅 续期后的期限: {extension_time}")
                # 记录新到期时间
                self.new_expiry_time = extension_time
            else:
                print("❌ 未找到时间内容")
            
        except Exception as e:
            print(f"❌ 记录续期后时间失败: {e}")
    
    async def find_final_extension_button(self):
        """查找并点击最终的期限延长按钮"""
        try:
            print("🔍 正在查找最终的'期限を延長する'按钮...")
            
            active_page = self.get_active_page()
            
            # 基于HTML属性查找按钮
            final_button_selector = "button[type='submit']:has-text('期限を延長する')"
            
            # 等待按钮出现
            await active_page.wait_for_selector(final_button_selector, timeout=self.wait_timeout)
            print("✅ 找到最终的'期限を延長する'按钮")
            
            # 点击按钮执行最终续期
            await active_page.click(final_button_selector)
            print("✅ 已点击最终续期按钮")
            
            # 等待页面跳转
            print("⏰ 等待续期操作完成...")
            await asyncio.sleep(5)
            
            # 验证续期结果
            await self.verify_extension_success()
            
            return True
            
        except Exception as e:
            print(f"❌ 执行最终期限延长操作失败: {e}")
            return False
    
    async def verify_extension_success(self):
        """验证续期操作是否成功"""
        try:
            print("🔍 正在验证续期操作结果...")
            
            active_page = self.get_active_page()
            current_url = active_page.url
            expected_url = "https://secure.xserver.ne.jp/xmgame/game/freeplan/extend/do"
            
            print(f"📍 当前页面URL: {current_url}")
            
            # 检查条件1：URL是否跳转到do页面
            url_success = expected_url in current_url
            
            # 检查条件2：是否有成功提示文字
            text_success = False
            try:
                success_text_selector = "p:has-text('期限を延長しました。')"
                await active_page.wait_for_selector(success_text_selector, timeout=5000)
                success_text = await active_page.query_selector(success_text_selector)
                if success_text:
                    text_content = await success_text.text_content()
                    print(f"✅ 找到成功提示文字: {text_content.strip()}")
                    text_success = True
            except Exception:
                print("ℹ️ 未找到成功提示文字")
            
            # 任意一项满足即为成功
            if url_success or text_success:
                print("🎉 续期操作成功！")
                if url_success:
                    print(f"✅ URL验证成功: {current_url}")
                if text_success:
                    print("✅ 成功提示文字验证成功")
                
                # 设置状态为成功
                self.renewal_status = "Success"
                await self.take_screenshot("extension_success")
                return True
            else:
                print("❌ 续期操作可能失败")
                print(f"   当前URL: {current_url}")
                print(f"   期望URL: {expected_url}")
                # 设置状态为失败
                self.renewal_status = "Failed"
                await self.take_screenshot("extension_failed")
                return False
                
        except Exception as e:
            print(f"❌ 验证续期结果失败: {e}")
            # 设置状态为失败
            self.renewal_status = "Failed"
            return False
    
    # =================================================================
    #                    6D. 结果记录与报告模块
    # =================================================================
    
    def generate_readme(self):
        """生成README.md文件记录续期情况"""
        try:
            print("📝 正在生成README.md文件...")
            
            # 获取当前时间
            # 使用北京时间（UTC+8）
            beijing_time = datetime.datetime.now(timezone(timedelta(hours=8)))
            current_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 根据状态生成不同的内容
            readme_content = f"**最后运行时间**: `{current_time}`\n\n"
            readme_content += "**运行结果**: <br>\n"
            readme_content += "🖥️服务器：`🇯🇵Xserver(Mc)`<br>\n"
            
            # 根据续期状态生成对应的结果
            if self.renewal_status == "Success":
                readme_content += "📊续期结果：✅Success<br>\n"
                readme_content += f"🕛️旧到期时间: `{self.old_expiry_time or 'Unknown'}`<br>\n"
                readme_content += f"🕡️新到期时间: `{self.new_expiry_time or 'Unknown'}`<br>\n"
            elif self.renewal_status == "Unexpired":
                readme_content += "📊续期结果：ℹ️Unexpired<br>\n"
                readme_content += f"🕛️旧到期时间: `{self.old_expiry_time or 'Unknown'}`<br>\n"
            elif self.renewal_status == "Failed":
                readme_content += "📊续期结果：❌Failed<br>\n"
                readme_content += f"🕛️旧到期时间: `{self.old_expiry_time or 'Unknown'}`<br>\n"
            else:
                readme_content += "📊续期结果：❓Unknown<br>\n"
                readme_content += f"🕛️旧到期时间: `{self.old_expiry_time or 'Unknown'}`<br>\n"
            
            # 写入README.md文件
            with open("README.md", "w", encoding="utf-8") as f:
                f.write(readme_content)
            
            print("✅ README.md文件生成成功")
            print(f"📄 续期状态: {self.renewal_status}")
            print(f"📅 原到期时间: {self.old_expiry_time or 'Unknown'}")
            if self.new_expiry_time:
                print(f"📅 新到期时间: {self.new_expiry_time}")
            
        except Exception as e:
            print(f"❌ 生成README.md文件失败: {e}")
    
    # =================================================================
    #                       7. 主流程控制模块
    # =================================================================
    
    async def run(self):
        """运行自动登录流程"""
        try:
            print("🚀 开始 XServer GAME 自动登录流程...")
            
            # 步骤1：验证配置
            if not self.validate_config():
                return False
            
            # 步骤2：设置浏览器
            if not await self.setup_browser():
                return False
            
            # 步骤3：导航到登录页面
            if not await self.navigate_to_login():
                return False
            
            # 步骤3.5：预先创建新标签页（用于邮箱验证）
            if not await self.prepare_new_tab():
                return False
            
            # 步骤4：执行登录操作
            if not await self.perform_login():
                return False
            
            # 步骤5：检查是否需要验证
            verification_result = await self.handle_verification_page()
            if verification_result:
                print("✅ 验证流程已处理")
                await asyncio.sleep(3)  # 等待验证完成后的页面跳转
            
            # 步骤6：检查登录结果
            if not await self.handle_login_result():
                print("⚠️ 登录可能失败，请检查邮箱和密码是否正确")
                return False
            
            print("🎉 XServer GAME 自动登录流程完成！")
            await self.take_screenshot("login_completed")
            
            # 生成README.md文件
            self.generate_readme()
            
            # 保持浏览器打开一段时间以便查看结果
            print("⏰ 浏览器将在 30 秒后关闭...")
            await asyncio.sleep(30)
            
            return True
            
        except Exception as e:
            print(f"❌ 自动登录流程出错: {e}")
            # 即使出错也生成README文件
            self.generate_readme()
            return False
        
        finally:
            await self.cleanup()


# =====================================================================
#                          主程序入口
# =====================================================================

async def main():
    """主函数"""
    print("=" * 60)
    print("XServer GAME 自动登录脚本 - Playwright版本")
    print("基于 Playwright + stealth")
    print("=" * 60)
    print()
    
    # 显示当前配置
    print("📋 当前配置:")
    print(f"   XServer邮箱: {LOGIN_EMAIL}")
    print(f"   XServer密码: {'*' * len(LOGIN_PASSWORD)}")
    print(f"   目标网站: {TARGET_URL}")
    print(f"   无头模式: {USE_HEADLESS}")
    print(f"   自动验证: 启用 (自动获取邮箱验证码)")
    print()
    print("📧 邮箱验证码配置:")
    print(f"   邮箱网站: {WEBMAIL_URL}")
    print(f"   登录用户: {WEBMAIL_USERNAME}")
    print(f"   邮箱密码: {'*' * len(WEBMAIL_PASSWORD)}")
    print(f"   目标邮箱: {TARGET_EMAIL}")
    print()
    
    # 确认配置
    if LOGIN_EMAIL == "your_email@example.com" or LOGIN_PASSWORD == "your_password":
        print("❌ 请先在代码开头的配置区域设置正确的邮箱和密码！")
        return
    
    print("🚀 配置验证通过，自动开始登录...")
    
    # 创建并运行自动登录器
    auto_login = XServerAutoLogin()
    
    # 启用自动验证码获取
    auto_login.use_auto_verification = True
    
    success = await auto_login.run()
    
    if success:
        print("✅ 登录流程执行成功！")
        exit(0)
    else:
        print("❌ 登录流程执行失败！")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
