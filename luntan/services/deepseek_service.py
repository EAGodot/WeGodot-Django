import requests
import json
import os
from django.conf import settings
from django.utils import timezone

class DeepSeekService:
    def __init__(self):
        self.api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        self.base_url = "https://api.deepseek.com/v1/chat/completions"  # 根据实际API调整
        
    def evaluate_survey_response(self, survey_title, standard_answers, user_answers):
        """
        评估问卷回答
        
        Args:
            survey_title: 问卷标题
            standard_answers: 标准答案
            user_answers: 用户回答
            
        Returns:
            dict: 包含评分和评语
        """
        if not self.api_key:
            raise Exception("DeepSeek API密钥未配置")
        
        # 构建评估提示
        prompt = self._build_evaluation_prompt(survey_title, standard_answers, user_answers)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",  # 根据实际模型调整
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的问卷评估专家。请根据标准答案对用户的问卷回答进行评分和评价。评分范围0-100分，评价要具体、有建设性。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # 解析AI返回的结果
            return self._parse_ai_response(ai_response)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"DeepSeek API请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"评估过程出错: {str(e)}")
    



    
    def _build_evaluation_prompt(self, survey_title, standard_answers, user_answers):
        """构建评估提示"""
        
        prompt = f"""
请对以下问卷回答进行评估：

问卷标题：{survey_title}

【标准答案参考】：
{json.dumps(standard_answers, ensure_ascii=False, indent=2)}

【用户回答】：
{json.dumps(user_answers, ensure_ascii=False, indent=2)}

评估要求：
1. 给出一个0-100分的总体评分
2. 提供具体的评语，包括：
- 回答的优点和亮点
- 需要改进的地方
- 建设性建议
3. 评分要客观公正，评语要具体有针对性

请按照以下JSON格式返回结果：
{{
    "score": 85.5,
    "comment": "具体的评语内容..."
}}

请确保返回的是纯JSON格式，不要包含其他文字。
"""
        return prompt
    





    def _parse_ai_response(self, ai_response):
        """解析AI返回的结果"""
        try:
            # 尝试直接解析JSON
            import re
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
            else:
                # 如果没有找到JSON，尝试手动解析
                result = self._manual_parse_response(ai_response)
            
            # 验证必要字段
            if 'score' not in result or 'comment' not in result:
                raise ValueError("AI返回结果缺少必要字段")
                
            # 确保评分在0-100之间
            score = float(result['score'])
            if score < 0:
                score = 0
            elif score > 100:
                score = 100
                
            return {
                'score': score,
                'comment': result['comment']
            }
            
        except Exception as e:
            # 如果解析失败，使用默认值
            return {
                'score': 0,
                'comment': f"评估结果解析失败: {str(e)}。原始响应: {ai_response[:500]}"
            }
    
    def _manual_parse_response(self, response_text):
        """手动解析响应文本"""
        result = {'score': 0, 'comment': response_text}
        
        # 尝试提取分数
        import re
        score_patterns = [
            r'评分[:：]\s*(\d+(?:\.\d+)?)',
            r'score[:：]\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*分'
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                try:
                    result['score'] = float(match.group(1))
                    break
                except ValueError:
                    continue
        
        return result