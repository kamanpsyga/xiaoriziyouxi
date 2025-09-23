#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
域名邮箱自动登录脚本
专门用于测试自建域名邮箱的自动登录和验证码提取
"""

import undetected_chromedriver as uc
import time
import re
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ================================
# 配置区域 - 请在这里设置您的邮箱信息
# ================================

# 邮箱登录配置
WEBMAIL_URL = "https://zmkk.edu.kg/login"  # 您的网页邮箱地址
EMAIL_ADDRESS = os.getenv("WEBMAIL_USERNAME", "kaixa913")  # 您的完整邮箱地址
EMAIL_PASSWORD = os.getenv("WEBMAIL_PASSWORD", "kaixa913!!")  # 您的邮箱密码

# 浏览器配置
USE_HEADLESS = False  # 是否使用无头模式（建议测试时设为False）
WAIT_TIMEOUT = 10     # 页面元素等待超时时间（秒）

# ================================
# 配置区域结束
# ================================


class WebmailAutoLogin:
    def __init__(self):
        """初始化邮箱自动登录器"""
        self.driver = None
        self.webmail_url = WEBMAIL_URL
        self.email = EMAIL_ADDRESS
        self.password = EMAIL_PASSWORD
        self.headless = USE_HEADLESS
        self.wait_timeout = WAIT_TIMEOUT
    
    def setup_driver(self):
        """设置Chrome驱动"""
        try:
            print("🚀 正在初始化Chrome浏览器...")
            
            options = uc.ChromeOptions()
            
            if self.headless:
                options.add_argument('--headless')
            
            # 基本Chrome选项
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-notifications')
            options.add_argument('--window-size=1200,800')
            
            # 创建Chrome实例
            self.driver = uc.Chrome(options=options)
            
            print("✅ Chrome浏览器初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ Chrome浏览器初始化失败: {e}")
            return False
    
    def navigate_to_webmail(self):
        """导航到邮箱登录页面"""
        try:
            print(f"🌐 正在访问邮箱: {self.webmail_url}")
            self.driver.get(self.webmail_url)
            
            # 等待页面加载
            WebDriverWait(self.driver, self.wait_timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            print("✅ 邮箱页面加载成功")
            return True
            
        except TimeoutException:
            print("❌ 邮箱页面加载超时")
            return False
        except Exception as e:
            print(f"❌ 访问邮箱失败: {e}")
            return False
    
    def find_login_form(self):
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
    
    
    def human_type(self, element, text):
        """模拟人类输入行为"""
        import random
        
        for char in text:
            element.send_keys(char)
            # 随机延迟，模拟真实打字速度
            delay = random.uniform(0.05, 0.2)
            time.sleep(delay)
    
    def perform_login(self):
        """执行邮箱登录"""
        try:
            # 查找登录表单
            email_input, password_input, login_button = self.find_login_form()
            
            if not email_input or not password_input:
                return False
            
            print("📝 正在填写登录信息...")
            
            # 填写邮箱
            email_input.clear()
            self.human_type(email_input, self.email)
            print("✅ 邮箱已填写")
            
            # 等待一下
            time.sleep(1)
            
            # 填写密码
            password_input.clear()
            self.human_type(password_input, self.password)
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
    
    def check_login_result(self):
        """检查登录结果"""
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
    
    def run_test(self):
        """运行完整的邮箱登录测试"""
        try:
            print("=" * 60)
            print("域名邮箱自动登录测试")
            print("=" * 60)
            print()
            
            # 显示配置信息
            print("📋 当前配置:")
            print(f"   邮箱地址: {self.webmail_url}")
            print(f"   用户邮箱: {self.email}")
            print(f"   密码: {'*' * len(self.password)}")
            print(f"   无头模式: {self.headless}")
            print()
            
            # 验证配置
            if not self.email or self.email == "your_email@zmkk.edu.kg":
                print("❌ 请先设置正确的邮箱地址！")
                return False
            
            if not self.password or self.password == "your_password":
                print("❌ 请先设置正确的邮箱密码！")
                return False
            
            # 1. 初始化浏览器
            if not self.setup_driver():
                return False
            
            # 2. 访问邮箱
            if not self.navigate_to_webmail():
                return False
            
            # 3. 执行登录
            if not self.perform_login():
                return False
            
            # 4. 检查登录结果
            if not self.check_login_result():
                print("⚠️ 邮箱登录可能失败")
                return False
            
            print("🎉 邮箱登录成功！")
            
            # 5. 选择目标邮箱
            if not self.select_target_mailbox():
                print("⚠️ 选择邮箱失败")
                return False
            
            # 6. 自动搜索验证邮件
            print()
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
                else:
                    print("⚠️ 未能提取到验证码")
            else:
                print("⚠️ 未找到验证邮件")
            
            # 保持浏览器打开
            print()
            print("⏰ 浏览器将保持打开状态，您可以手动查看邮箱")
            input("按回车键关闭浏览器...")
            
            return True
            
        except Exception as e:
            print(f"❌ 测试过程出错: {e}")
            return False
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            try:
                # 先关闭所有窗口
                self.driver.close()
                # 然后退出驱动
                self.driver.quit()
                print("🧹 浏览器已关闭")
            except Exception as e:
                print(f"⚠️ 关闭浏览器时出错: {e}")
            finally:
                self.driver = None


def main():
    """主函数"""
    webmail_login = WebmailAutoLogin()
    success = webmail_login.run_test()
    
    if success:
        print("✅ 邮箱登录测试完成！")
    else:
        print("❌ 邮箱登录测试失败！")


if __name__ == "__main__":
    main()
