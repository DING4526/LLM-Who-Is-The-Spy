# LLM WHO IS THE SPY

一个由大语言模型驱动的AI版谁是卧底对战框架

## 游戏主体

`game.py` 谁是卧底游戏主程序

`player.py` 参与游戏的LLM智能体

`game_record.py` 用于保存和提取游戏记录

`llm_client.py` 用于配置模型接口和发起LLM请求

`prompt/` 保存了各种提示词模板

## 配置

使用conda环境配置相应依赖包：

```
pip install openai
```

本项目的API配置在`llm_client.py`中。

本项目利用了One API https://github.com/songquanpeng/one-api 实现统一的接口调用。使用时需自行配置相应模型的API接口。

## 使用方法

### 运行

完成项目配置后，在`game.py`和`multi_game_runner.py`主程序入口的`player_configs`中设置正确的模型名称

运行游戏：
```
python game.py
```
