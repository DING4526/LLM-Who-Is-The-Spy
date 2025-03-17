import random
from typing import List, Dict

import game_record
from player import Player
from game_record import GameRecord, PlayerInitialState

# 定义关键词常量
SPY_KEYWORD = "狼人杀"
CIVIL_KEYWORD = "剧本杀"


class Game:
    def __init__(self, player_configs: List[Dict[str, str]]) -> None:
        """
        初始化游戏

        Args:
            player_configs: 包含玩家配置的列表，每个配置是一个字典，包含 name 和 model 字段
        """
        # 使用配置创建玩家对象
        self.player_list = [Player(config["name"], config["model"]) for config in player_configs]

        self.spy_name: str = ""
        self.game_over: bool = False
        self.winner: str = ""
        self.round_count = 0

        # GameRecord 对象在游戏开始后创建
        self.game_record: GameRecord = None

    def create_keywords(self):
        """为每个玩家分配词语"""
        # 随机选择卧底玩家
        spy_idx = random.randint(0, len(self.player_list) - 1)
        self.spy_name = self.player_list[spy_idx].name
        for player in self.player_list:
            if player.name == self.spy_name:
                player.keyword = SPY_KEYWORD
            else:
                player.keyword = CIVIL_KEYWORD

        print(f"[关键词分配] 卧底是 {self.spy_name}")
        for player in self.player_list:
            print(f"玩家 {player.name} 的关键词是 {player.keyword}")

    def start_round_record(self) -> None:
        """开始新的回合，并在 GameRecord 中记录信息"""
        self.round_count += 1
        while True:
            starting_player_idx = random.randint(0, len(self.player_list) - 1)
            if self.player_list[starting_player_idx].alive:
                break
        self.game_record.start_new_round(self.round_count, starting_player_idx)

    def is_valid_play(self, current_player:Player, description:str) -> bool:
        """
        判断发言是否符合规则

        Returns:
            bool: 是否符合规则
        """
        if not description:
            return False
        # for word in current_player.keyword:
        #     if word in description:
        #         return False
        if current_player.keyword in description:
            return False
        return True

    def find_next_player_alive(self, start_idx: int) -> int:
        """返回下一个存活的玩家索引"""
        idx = start_idx
        for _ in range(len(self.player_list)):
            idx = (idx + 1) % len(self.player_list)
            if self.player_list[idx].alive:
                return idx
        return start_idx  # 理论上不会发生

    def check_vote_result(self):
        """
        根据当前回合记录的所有投票，统计票数并淘汰获得最多票数的玩家
        如果票数相同，则随机选择一名
        """
        current_round = self.game_record.get_current_round()
        vote_counts = {}
        for vote in current_round.votes:
            voted = vote["voted_player"]
            vote_counts[voted] = vote_counts.get(voted, 0) + 1

        if not vote_counts:
            print("本轮没有投票记录。")
            return
        print(f"[投票结果] {vote_counts}")

        # 找出票数最多的玩家
        max_votes = max(vote_counts.values())
        candidates = [p for p, count in vote_counts.items() if count == max_votes]
        eliminated_player_name = random.choice(candidates)

        # 记录投票结果
        self.game_record.get_current_round().add_voting_result(vote_counts,eliminated_player_name)

        # 设置对应玩家死亡
        for player in self.player_list:
            if player.name == eliminated_player_name:
                player.alive = False
                print(f"[投票结果] 玩家 {player.name} 被淘汰！")
                break

    def handle_perform(self, current_player: Player) -> str:
        """
        处理玩家发言环节
        """
        # 传入当前玩家列表以获取存活玩家信息
        round_base_info = self.game_record.get_round_base_info(self.player_list)
        previous_info = self.game_record.get_previous_info(current_player)

        performance, reasoning = current_player.perform(round_base_info, previous_info)
        # 记录发言记录到当前回合中
        self.game_record.get_current_round().add_performance(
            player_name=current_player.name,
            description=performance.get("description", ""),
            tendency=performance.get("tendency", ""),
            self_prediction=performance.get("self_prediction", False),
            keyword_prediction=performance.get("keyword_prediction", "")
        )
        return performance["description"]

    def handle_vote(self, current_player: Player):
        """
        处理玩家投票环节

        Args:
            current_player: 当前玩家（进行投票的玩家）
        假设玩家的 vote 方法返回 (result, reasoning, prompt)
        """
        round_base_info = self.game_record.get_round_base_info(self.player_list)
        previous_info = self.game_record.get_previous_info(current_player)

        result, reasoning = current_player.vote(round_base_info, previous_info)
        # 记录投票记录到当前回合中
        self.game_record.get_current_round().add_vote(
            player_name=current_player.name,
            voted_player=result.get("voted_player", ""),
            vote_reason=result.get("vote_reason", "")
        )
        # return result["voted_player"], result["vote_reason"]

    def play_round(self) -> None:
        """执行一轮游戏逻辑：先发言，再投票，最后处理投票结果"""
        starting_player_idx = self.game_record.get_current_round().starting_player_idx
        current_player_idx = starting_player_idx

        print(f"\n【第 {self.round_count} 轮】 发言阶段开始")
        # 发言阶段，每个存活玩家依次发言
        while True:
            current_player = self.player_list[current_player_idx]
            if current_player.alive:
                print(f"\n轮到 {current_player.name} 发言, 关键词：{current_player.keyword}")
                description = self.handle_perform(current_player)
                if not self.is_valid_play(current_player,description):
                    print(f"玩家 {current_player.name} 的发言不符合规则！")

            # 找到下一个存活玩家
            next_idx = self.find_next_player_alive(current_player_idx)
            print("next_player",self.player_list[next_idx].name)
            print("starting_player",self.player_list[starting_player_idx].name)
            # 若回到起始玩家，则结束发言阶段
            if next_idx == starting_player_idx:
                break
            current_player_idx = next_idx

        print(f"\n【第 {self.round_count} 轮】 投票阶段开始")
        # 投票阶段，重置索引
        current_player_idx = starting_player_idx
        while True:
            current_player = self.player_list[current_player_idx]
            if current_player.alive:
                print(f"\n轮到 {current_player.name} 投票, 关键词：{current_player.keyword}")
                self.handle_vote(current_player)
            next_idx = self.find_next_player_alive(current_player_idx)
            if next_idx == starting_player_idx:
                break
            current_player_idx = next_idx

        # 处理投票结果
        self.check_vote_result()
        self.check_victory()

    def start_game(self) -> None:
        """启动游戏主循环"""
        self.create_keywords()
        # 创建游戏记录对象，记录每个玩家初始状态
        from game_record import PlayerInitialState  # 已经导入
        initial_states = [PlayerInitialState(player.name, player.keyword, player.model_name)
                          for player in self.player_list]
        self.game_record = GameRecord(initial_states,CIVIL_KEYWORD,SPY_KEYWORD)

        # 开始第一回合记录
        self.start_round_record()

        while not self.game_over:
            self.play_round()
            # 如果游戏没有结束，则开始新一回合
            if not self.game_over:
                self.start_round_record()

    def check_victory(self) -> bool:
        """
        检查胜利条件（仅剩一名存活玩家时），并记录胜利者

        Returns:
            bool: 游戏是否结束
        """
        alive_players = [p for p in self.player_list if p.alive]
        spy_is_alive = self.spy_name in [p.name for p in alive_players]
        if not spy_is_alive or len(alive_players) <= 3:
            self.winner = "卧底" if spy_is_alive else "平民"
            print(f"\n【游戏结束】 {self.winner} 获胜！")
            self.game_over = True
            self.game_record.record_winner(self.winner)
            self.game_record.export_record()
            return True
        return False


if __name__ == '__main__':
    # 配置玩家信息，model 为调用 AI 模型时使用的模型名称
    player_configs = [
        # {
        #     "name": "GPT-4o-mini",
        #     "model": "gpt-4o-mini"
        # },
        {
            "name": "Qwen-32B-Instruct",
            "model": "Qwen/Qwen2.5-32B-Instruct"
        },
        {
            "name": "Qwen-32B",
            "model": "Qwen/QwQ-32B"
        },
        # {
        #     "name": "DeepSeek-R1-7B",
        #     "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
        # },
        # {
        #     "name": "DeepSeek-R1-14B",
        #     "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B"
        # },
        {
            "name": "DeepSeek-R1-32B",
            "model": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
        },
        {
            "name": "DeepSeek-V2.5",
            "model": "deepseek-ai/DeepSeek-V2.5"
        },
        {
            "name": "DeepSeek-V3",
            "model": "deepseek-ai/DeepSeek-V3"
        },
        {
            "name": "DeepSeek-R1",
            "model": "deepseek-reasoner"
        },
    ]

    print("游戏开始！玩家配置如下：")
    for config in player_configs:
        print(f"玩家：{config['name']}, 使用模型：{config['model']}")
    print("-" * 50)

    # 创建游戏实例并启动游戏
    game = Game(player_configs)
    game.start_game()
