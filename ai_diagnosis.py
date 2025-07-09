"""
AI诊断模块 - SiliconFlow API集成版本
与SiliconFlow大模型接入进行视力诊断分析
"""
import json
import requests
import time
from typing import List, Tuple, Dict, Optional

class AIVisionDiagnosis:
    """AI视力诊断类"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "Qwen/Qwen3-8B",
                 progress_callback=None, stream_callback=None):
        """
        初始化AI诊断模块

        Args:
            api_key: SiliconFlow API密钥
            model: 使用的模型名称，默认使用Qwen3-8B（速度快，质量好）
            progress_callback: 进度回调函数，用于显示API调用进度
            stream_callback: 流式输出回调函数，用于实时显示生成的内容
        """
        self.api_key = api_key
        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.model = model
        self.use_real_api = api_key is not None and len(api_key) > 10
        self.progress_callback = progress_callback
        self.stream_callback = stream_callback

    def check_network_connection(self) -> bool:
        """检查网络连接"""
        try:
            # 尝试连接到SiliconFlow的基础URL
            response = requests.get("https://api.siliconflow.cn", timeout=5)
            return response.status_code in [200, 404]  # 404也表示能连接到服务器
        except:
            return False

    def test_api_connectivity(self) -> tuple[bool, str]:
        """测试API连接性"""
        if not self.use_real_api:
            return False, "未配置API密钥"

        if not self.check_network_connection():
            return False, "网络连接失败"

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 使用最小的测试请求
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
                "stream": False
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                return True, "API连接正常"
            elif response.status_code == 401:
                return False, "API密钥无效"
            elif response.status_code == 429:
                return False, "API调用频率限制"
            else:
                return False, f"API错误: HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "API连接超时"
        except Exception as e:
            return False, f"连接测试失败: {str(e)}"
        
    def analyze_vision_results(self, test_results: List[Tuple[float, bool]],
                             patient_info: Dict = None) -> str:
        """
        分析视力测试结果并生成AI诊断报告

        Args:
            test_results: 测试结果列表 [(vision_value, success), ...]
            patient_info: 患者信息字典

        Returns:
            str: AI诊断报告
        """
        # 构建分析数据
        analysis_data = self.prepare_analysis_data(test_results, patient_info)

        # 如果使用真实API，先进行连接性检查
        if self.use_real_api:
            print("🔍 正在检查API连接性...")
            is_connected, connection_msg = self.test_api_connectivity()
            if not is_connected:
                print(f"❌ API连接检查失败: {connection_msg}")
                return self.generate_fallback_diagnosis_with_error(f"API连接失败: {connection_msg}")
            else:
                print(f"✅ {connection_msg}")

        # 生成诊断提示词
        prompt = self.generate_diagnosis_prompt(analysis_data)

        # 调用AI接口
        try:
            diagnosis = self.call_ai_api(prompt)
        except Exception as e:
            print(f"AI接口调用失败: {e}")
            diagnosis = self.generate_fallback_diagnosis(analysis_data)

        return diagnosis
    
    def prepare_analysis_data(self, test_results: List[Tuple[float, bool]], 
                            patient_info: Dict = None) -> Dict:
        """准备分析数据"""
        if not test_results:
            return {"error": "无测试数据"}
        
        # 计算统计信息
        total_tests = len(test_results)
        successful_tests = sum(1 for _, success in test_results if success)
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # 找到最高成功视力值
        max_successful_vision = 0
        for vision_value, success in test_results:
            if success and vision_value > max_successful_vision:
                max_successful_vision = vision_value
        
        # 分析视力趋势
        vision_trend = self.analyze_vision_trend(test_results)
        
        analysis_data = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "max_successful_vision": max_successful_vision,
            "vision_trend": vision_trend,
            "test_results": test_results,
            "patient_info": patient_info or {}
        }
        
        return analysis_data
    
    def analyze_vision_trend(self, test_results: List[Tuple[float, bool]]) -> str:
        """分析视力变化趋势"""
        if len(test_results) < 2:
            return "数据不足"
        
        successful_visions = [vision for vision, success in test_results if success]
        
        if len(successful_visions) < 2:
            return "成功测试数据不足"
        
        if successful_visions[-1] > successful_visions[0]:
            return "视力呈上升趋势"
        elif successful_visions[-1] < successful_visions[0]:
            return "视力呈下降趋势"
        else:
            return "视力保持稳定"
    
    def generate_diagnosis_prompt(self, analysis_data: Dict) -> str:
        """生成AI诊断提示词"""
        prompt = f"""
作为专业的眼科医生，请根据以下视力测试数据进行分析和诊断：

测试统计：
- 总测试次数: {analysis_data['total_tests']}
- 成功测试次数: {analysis_data['successful_tests']}
- 成功率: {analysis_data['success_rate']:.2%}
- 最高成功视力值: {analysis_data['max_successful_vision']}
- 视力趋势: {analysis_data['vision_trend']}

详细测试结果：
"""
        
        for i, (vision, success) in enumerate(analysis_data['test_results']):
            status = "成功" if success else "失败"
            prompt += f"- 测试{i+1}: 视力{vision} - {status}\n"
        
        prompt += """
请提供以下内容：
1. 视力状况评估
2. 可能的原因分析
3. 建议的后续行动
4. 日常护眼建议
5. 是否需要进一步检查

请用专业但易懂的语言回答，字数控制在300字以内。
"""
        
        return prompt
    
    def call_ai_api(self, prompt: str) -> str:
        """调用SiliconFlow API进行AI诊断（优化版本）"""
        if not self.use_real_api:
            print("使用模拟诊断（未配置API密钥）")
            return self.generate_mock_diagnosis()

        # 记录开始时间
        start_time = time.time()

        # 多次重试机制，使用更长的超时时间
        max_retries = 2  # 减少重试次数，但使用更长超时
        timeout_values = [30, 60]  # 更长的超时时间

        for attempt in range(max_retries):
            try:
                timeout = timeout_values[attempt]
                progress_msg = f"正在调用AI诊断服务... 尝试 {attempt + 1}/{max_retries} (预计等待: {timeout}秒)"
                print(progress_msg)

                # 调用进度回调
                if self.progress_callback:
                    self.progress_callback(progress_msg)

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "VisionTest/1.0"
                }

                # 简化的请求数据，启用流式传输
                use_stream = self.stream_callback is not None
                data = {
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": f"作为眼科医生，简要分析视力测试结果并给出建议（200字内）：{prompt[:500]}"
                        }
                    ],
                    "stream": use_stream,  # 根据是否有回调决定是否使用流式
                    "max_tokens": 300,
                    "temperature": 0.1,
                    "top_p": 0.7
                }

                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=timeout,
                    stream=use_stream  # 启用流式响应
                )

                if response.status_code == 200:
                    if use_stream:
                        # 流式处理
                        diagnosis = self.handle_stream_response(response)
                        if diagnosis:
                            print("✅ AI诊断获取成功（流式）")
                            return diagnosis
                        else:
                            print("⚠️ 流式响应处理失败")
                            if attempt == max_retries - 1:
                                return self.generate_fallback_diagnosis_with_error("流式响应处理失败")
                            continue
                    else:
                        # 非流式处理
                        result = response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            diagnosis = result['choices'][0]['message']['content']
                            print("✅ AI诊断获取成功")
                            return diagnosis
                        else:
                            print("⚠️ API响应格式异常")
                            if attempt == max_retries - 1:
                                return self.generate_fallback_diagnosis_with_error("API响应格式异常")
                            continue

                elif response.status_code == 401:
                    error_msg = "API密钥无效或已过期"
                    print(f"❌ {error_msg}")
                    return self.generate_fallback_diagnosis_with_error(error_msg)

                elif response.status_code == 429:
                    error_msg = "API调用频率限制，请稍后重试"
                    print(f"⚠️ {error_msg}")
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)  # 指数退避
                        continue
                    return self.generate_fallback_diagnosis_with_error(error_msg)

                else:
                    error_msg = f"API调用失败: HTTP {response.status_code}"
                    if response.text:
                        try:
                            error_data = response.json()
                            if 'error' in error_data:
                                error_msg += f" - {error_data['error'].get('message', '未知错误')}"
                        except:
                            error_msg += f" - {response.text[:100]}"

                    print(f"⚠️ {error_msg}")
                    if attempt == max_retries - 1:
                        return self.generate_fallback_diagnosis_with_error(error_msg)
                    continue

            except requests.exceptions.Timeout:
                error_msg = f"API调用超时 (超时时间: {timeout}秒)"
                print(f"⏰ {error_msg}")
                if attempt == max_retries - 1:
                    return self.generate_fallback_diagnosis_with_error("API调用超时，请检查网络连接")
                continue

            except requests.exceptions.ConnectionError:
                error_msg = "网络连接错误，请检查网络设置"
                print(f"🌐 {error_msg}")
                if attempt == max_retries - 1:
                    return self.generate_fallback_diagnosis_with_error(error_msg)
                continue

            except requests.exceptions.RequestException as e:
                error_msg = f"网络请求错误: {str(e)}"
                print(f"🌐 {error_msg}")
                if attempt == max_retries - 1:
                    return self.generate_fallback_diagnosis_with_error(error_msg)
                continue

            except Exception as e:
                error_msg = f"API调用异常: {str(e)}"
                print(f"❌ {error_msg}")
                if attempt == max_retries - 1:
                    return self.generate_fallback_diagnosis_with_error(error_msg)
                continue

        # 如果所有重试都失败了
        return self.generate_fallback_diagnosis_with_error("多次重试后仍然失败，请稍后再试")

    def handle_stream_response(self, response) -> str:
        """处理流式响应"""
        try:
            import json

            full_content = ""

            # 通知开始流式输出
            if self.stream_callback:
                self.stream_callback("开始接收AI诊断结果...\n\n", is_start=True)

            # 处理流式数据
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')

                    # 跳过非数据行
                    if not line.startswith('data: '):
                        continue

                    # 移除 'data: ' 前缀
                    data_str = line[6:]

                    # 检查是否是结束标记
                    if data_str.strip() == '[DONE]':
                        break

                    try:
                        # 解析JSON数据
                        data = json.loads(data_str)

                        # 提取内容
                        if 'choices' in data and len(data['choices']) > 0:
                            delta = data['choices'][0].get('delta', {})
                            content = delta.get('content', '')

                            if content:
                                full_content += content

                                # 实时回调显示内容
                                if self.stream_callback:
                                    self.stream_callback(content, is_chunk=True)

                                # 也在控制台显示（可选）
                                print(content, end='', flush=True)

                    except json.JSONDecodeError:
                        # 跳过无法解析的行
                        continue

            # 通知流式输出结束
            if self.stream_callback:
                self.stream_callback("", is_end=True)

            print()  # 换行
            return full_content.strip()

        except Exception as e:
            print(f"流式响应处理错误: {e}")
            return None
    
    def generate_fallback_diagnosis_with_error(self, error_msg: str) -> str:
        """生成包含错误信息的备用诊断"""
        return f"""
**AI诊断服务暂时不可用**

错误信息: {error_msg}

**基于测试结果的基础分析:**
根据您的视力测试表现，建议：

1. **如果测试结果良好（视力5.0以上）**：
   - 视力状况优秀，请继续保持良好的用眼习惯
   - 定期进行视力检查，建议每年1-2次

2. **如果测试结果一般（视力4.5-5.0）**：
   - 视力状况良好，注意用眼卫生
   - 避免长时间近距离用眼，适当休息

3. **如果测试结果较差（视力4.5以下）**：
   - 建议到专业眼科医院进行详细检查
   - 可能需要配镜或其他矫正措施

**通用护眼建议:**
- 遵循20-20-20法则：每20分钟看20英尺外的物体20秒
- 保持充足的睡眠和均衡的营养
- 适当进行户外活动
- 定期进行眼部检查

*注：此为基础建议，详细诊断请咨询专业眼科医生。*
"""

    def generate_mock_diagnosis(self) -> str:
        """生成模拟诊断（用于演示）"""
        return """
基于您的视力测试结果，AI诊断分析如下：

**视力状况评估：**
根据测试数据显示，您的视力水平处于正常范围内，但存在轻微的视力波动。

**可能原因分析：**
1. 用眼疲劳：长时间使用电子设备可能导致视力暂时性下降
2. 环境因素：测试环境的光线条件可能影响结果
3. 注意力集中度：测试过程中的专注程度会影响准确性

**建议的后续行动：**
1. 建议3-6个月后进行复查，监测视力变化趋势
2. 如有视力下降症状加重，应及时就医
3. 保持良好的用眼习惯

**日常护眼建议：**
1. 遵循20-20-20法则：每20分钟看20英尺外的物体20秒
2. 保证充足的睡眠和均衡的营养
3. 适当进行户外活动，增加自然光照射
4. 定期进行眼部按摩和眼保健操

**进一步检查建议：**
目前测试结果基本正常，暂不需要特殊检查。如有不适症状，建议到专业眼科进行详细检查。

*注：此诊断仅供参考，如有疑虑请咨询专业眼科医生。*
"""
    
    def generate_fallback_diagnosis(self, analysis_data: Dict) -> str:
        """生成备用诊断（当AI接口不可用时）"""
        max_vision = analysis_data.get('max_successful_vision', 0)
        success_rate = analysis_data.get('success_rate', 0)
        
        if max_vision >= 5.0:
            vision_level = "优秀"
            advice = "请继续保持良好的用眼习惯。"
        elif max_vision >= 4.5:
            vision_level = "良好"
            advice = "注意用眼卫生，避免长时间用眼。"
        elif max_vision >= 4.0:
            vision_level = "一般"
            advice = "建议加强眼部保健，必要时考虑配镜。"
        else:
            vision_level = "较差"
            advice = "建议尽快到眼科医院进行详细检查。"
        
        diagnosis = f"""
**视力测试结果分析**

测试完成度: {success_rate:.1%}
最佳视力值: {max_vision}
视力水平: {vision_level}

**基础建议:**
{advice}

**通用护眼建议:**
1. 保持适当的阅读距离（33-40cm）
2. 确保充足的照明条件
3. 定期休息，避免视疲劳
4. 多进行户外活动
5. 定期进行视力检查

*注：此为基础分析，详细诊断请咨询专业医生。*
"""
        
        return diagnosis



