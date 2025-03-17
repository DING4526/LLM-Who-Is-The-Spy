import datetime
import json
import os

from player import Player
from typing import List

def generate_game_id():
    """生成包含时间信息的游戏ID"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return timestamp

class PlayerInitialState:
    def __init__(self, name: str, keyword: str, model: str) -> None:
        self.name = name
        self.keyword = keyword
        self.model = model

    def to_dict(self):
        return {
            "name": self.name,
            "keyword": self.keyword,
            "model": self.model
        }

class RoundRecord:
    def __init__(self, round_number: int, starting_player_idx: int):
        self.round_number = round_number
        self.starting_player_idx = starting_player_idx
        self.performances = []  # 每个发言记录: {player, description, tendency, self_prediction, keyword_prediction}
        self.votes = []         # 每个投票记录: {player, voted_player, vote_reason}
        self.voting_result = {}

    def add_performance(self, player_name: str, description: str, tendency: str, self_prediction: bool,keyword_prediction:str):
        self.performances.append({
            "player": player_name,
            "description": description,
            "tendency": tendency,
            "self_prediction:": self_prediction,
            "keyword_prediction:":keyword_prediction
        })

    def add_vote(self, player_name: str, voted_player: str, vote_reason: str):
        self.votes.append({
            "player": player_name,
            "voted_player": voted_player,
            "vote_reason": vote_reason
        })

    def add_voting_result(self,vote_counts:dict[str,int],voted_player:str):
        self.voting_result={
            "vote_counts":vote_counts,
            "voted_player":voted_player
        }

    def to_dict(self):
        return {
            "round_number": self.round_number,
            "starting_player_idx": self.starting_player_idx,
            "performances": self.performances,
            "votes": self.votes,
            "voting_result":self.voting_result
        }




class GameRecord:
    def __init__(self, player_initial_states: List[PlayerInitialState],civil_keyword:str,spy_keyword:str) -> None:
        self.game_id = generate_game_id()+"_"+civil_keyword+"_"+spy_keyword
        self.save_directory: str = "game_records"
        # 记录每个玩家初始状态，按玩家名字建立字典
        self.player_initial_states = {p.name: p for p in player_initial_states}
        self.round_records: List[RoundRecord] = []
        self.winner: str = None

    def start_new_round(self, round_number: int, starting_player_idx: int):
        new_round = RoundRecord(round_number, starting_player_idx)
        self.round_records.append(new_round)

    def get_current_round(self) -> RoundRecord:
        return self.round_records[-1]

    def record_winner(self, winner_name: str):
        self.winner = winner_name

    def export_record(self) -> None:
        """导出整个游戏记录为 JSON 格式字符串"""
        record_data = {
            "game_id": self.game_id,
            "players": {name: state.to_dict() for name, state in self.player_initial_states.items()},
            "rounds": [round_rec.to_dict() for round_rec in self.round_records],
            "winner": self.winner
        }
        file_path = os.path.join(self.save_directory, f"{self.game_id}.json")
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(record_data, file, indent=4, ensure_ascii=False)
        print(f"游戏记录已自动保存至 {file_path}")

    def get_round_base_info(self, players_list: List["Player"]) -> str:
        """
        游戏情况如下：
        这是游戏的第{round_count}轮
        场上还剩下{player_list}，共{player_count}人

        返回一个 JSON 字符串，其中包含上述信息
        """
        current_round = self.get_current_round()
        round_count = current_round.round_number
        # 根据 players_list 的 alive 属性筛选出存活玩家
        alive_players = [player.name for player in players_list if player.alive]
        player_count = len(alive_players)

        round_base_info = {
            "round_count": round_count,
            "player_list": alive_players,
            "player_count": player_count
        }
        return json.dumps(round_base_info, ensure_ascii=False)

    def get_previous_info(self,current_player:Player):
        """
        此前大家的发言和表现如下：
        {previous_info}

        返回一个 JSON 字符串，记录各个轮次每个玩家的 performance
        """
        previous_info = []

        # 遍历所有轮次的发言和表现
        for round_record in self.round_records:
            round_record_info={
                "round_id":self.get_current_round().round_number,
                "previous_performance_info":[],
                "voting_result_info":{}
            }
            for performance in round_record.performances:
                record = {
                    "player": performance["player"],
                    "description": performance["description"],
                    "tendency": performance.get("tendency","")
                }
                if performance["player"] == current_player.name:
                    record["self_prediction"] = performance.get("self_prediction:", False)
                    record["keyword_prediction"] = performance.get("keyword_prediction:", "")
                round_record_info["previous_performance_info"].append(record)
            round_record_info["voting_result_info"]=round_record.voting_result
            previous_info.append(round_record_info)

        return json.dumps(previous_info, ensure_ascii=False)


