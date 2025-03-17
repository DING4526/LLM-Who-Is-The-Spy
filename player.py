import random
import json
import re
from typing import List, Dict, Tuple
from llm_client import LLMClient

RULE_BASE_PATH = "prompt/rule_base.txt"
PERFORM_PROMPT_TEMPLATE_PATH = "prompt/perform_prompt_template.txt"
VOTE_PROMPT_TEMPLATE_PATH = "prompt/vote_prompt_template.txt"


class Player:
    def __init__(self, name: str, model_name: str):
        """
        初始化玩家

        Args:
            name: 玩家名称
            model_name: 使用的LLM模型名称
        """
        self.name = name
        self.role = ""
        self.alive = True
        self.keyword = ""
        self.opinions = {}

        # 初始化LLM客户端
        self.llm_client = LLMClient()
        self.model_name = model_name

    def _read_file(self, filepath: str) -> str:
        """
        读取文件内容

        Args:
            filepath: 文件路径

        Returns:
            文件内容字符串
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"读取文件 {filepath} 失败: {str(e)}")
            return ""

    def perform(self,
                round_base_info: str,
                previous_info: str
                ) -> Tuple[Dict, str]:
        """
        玩家发言
        调用LLM接口生成决策，并返回解析后的JSON结果和LLM的原始推理内容。

        Returns:
            tuple: (结果字典, 推理内容)
        Raises:
            RuntimeError: 多次尝试后仍无法获取符合要求的结果
        """
        # 读取规则和模板
        rules = self._read_file(RULE_BASE_PATH)
        template = self._read_file(PERFORM_PROMPT_TEMPLATE_PATH)

        round_info = json.loads(round_base_info)
        round_count = round_info.get("round_count")
        player_list = round_info.get("player_list")
        player_count = round_info.get("player_count")

        # print(previous_info)
        previous = "你是整局游戏第一位发言的玩家，还没有任何发言记录，请谨慎发言，防止直接暴露" if previous_info == '[{"round_id": 1, "previous_performance_info": [], "voting_result_info": {}}]' else previous_info

        # 填充模板，此处可以根据实际需要补充更多上下文信息
        prompt = template.format(
            rules=rules,
            self_name=self.name,
            self_keyword=self.keyword,
            round_count=round_count,
            player_list=player_list,
            player_count=player_count,
            previous_info=previous
        )

        # 尝试获取有效的JSON响应，最多重试十次
        for attempt in range(10):
            messages = [
                {"role": "user", "content": prompt}
            ]
            try:
                content, reasoning_content = self.llm_client.chat(messages, model=self.model_name)
                # 提取JSON部分
                json_match = re.search(r'({[\s\S]*})', content)
                if json_match:
                    json_str = json_match.group(1)
                    result = json.loads(json_str)
                    # 验证JSON格式是否符合要求
                    if all(key in result for key in
                           ["description", "tendency", "self_prediction", "keyword_prediction", "perform_reason"]):
                        return result, reasoning_content
                    else:
                        prompt += f'\n\n【警告】请注意输出的格式要求：包含"description", "tendency", "self_prediction", "keyword_prediction", "perform_reason"五个字段'
                        print(f"玩家 {self.name} 的 perform 返回了错误的 json 格式")
            except Exception as e:
                print(f"玩家 {self.name} 的 perform 尝试 {attempt + 1} 解析失败: {str(e)}")
        raise RuntimeError(f"玩家 {self.name} 的 perform 方法在多次尝试后失败")

    def vote(self,
             round_base_info: str,
             previous_info: str
             ) -> Tuple[Dict, str]:
        """
        玩家投票
        调用LLM接口生成决策，并返回解析后的JSON结果和LLM的原始推理内容。

        Args:
            round_base_info:
            previous_info:

        Returns:
            tuple: (结果字典, 推理内容)
                - 结果字典应包含 "voted_player" 和 "vote_reason" 两个键
                - 推理内容为LLM的原始推理过程
        Raises:
            RuntimeError: 多次尝试后仍无法获取符合要求的结果
        """
        # 读取规则和模板
        rules = self._read_file(RULE_BASE_PATH)
        template = self._read_file(VOTE_PROMPT_TEMPLATE_PATH)

        round_info = json.loads(round_base_info)
        round_count = round_info.get("round_count")
        player_list = round_info.get("player_list")
        player_count = round_info.get("player_count")

        # 填充模板，此处可以根据实际需要补充更多上下文信息
        prompt = template.format(
            rules=rules,
            self_name=self.name,
            self_keyword=self.keyword,
            round_count=round_count,
            player_list=player_list,
            player_count=player_count,
            previous_info=previous_info
        )

        # 尝试获取有效的JSON响应，最多重试十次
        for attempt in range(10):
            messages = [
                {"role": "user", "content": prompt}
            ]
            try:
                content, reasoning_content = self.llm_client.chat(messages, model=self.model_name)
                json_match = re.search(r'({[\s\S]*})', content)
                if json_match:
                    json_str = json_match.group(1)
                    result = json.loads(json_str)
                    # 验证JSON格式是否符合要求
                    if all(key in result for key in ["voted_player", "vote_reason"]):
                        # 检查被投票玩家是否在当前游戏中（通过名称判断）
                        valid_player_names = [p for p in player_list]
                        if result["voted_player"] in valid_player_names:
                            return result, reasoning_content
                        else:
                            prompt += "\n\n【警告】你不能投票给已经淘汰的玩家"
                            print(f"玩家 {self.name} 的 vote 返回了无效的 voted_player: {result['voted_player']}")
            except Exception as e:
                print(f"玩家 {self.name} 的 vote 尝试 {attempt + 1} 解析失败: {str(e)}")
        raise RuntimeError(f"玩家 {self.name} 的 vote 方法在多次尝试后失败")
