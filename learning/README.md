# Agent Study 学习中心

> 更新日期：2026-07-03  
> 学习项目：`pguso/agents-from-scratch`  
> 本地模型：Llama 3 8B Instruct，Q4_K_M GGUF

`learning/` 是本项目唯一的学习资料入口，用来统一保存技术路线、个人进度和后续教授他人的教学方法。

## 文档导航

| 文档 | 用途 | 更新时机 |
| --- | --- | --- |
| [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md) | 相对稳定的 Agent 技术路线和阶段目标 | 技术方向变化时 |
| [LEARNING_PROGRESS.md](LEARNING_PROGRESS.md) | 当前课程进度、证据、薄弱点和下一步 | 每次学习结束后 |
| [TEACHING_GUIDE.md](TEACHING_GUIDE.md) | 后续教授他人时使用的固定教学流程 | 验证出新的有效教学方法后 |
| [notes/LESSON_TEMPLATE.md](notes/LESSON_TEMPLATE.md) | 每课学习笔记模板 | 很少修改 |

## 当前快照

- Python、本地推理环境和 GGUF 模型已经配置并运行成功。
- Lesson 01-10 均有独立练习文件和运行证据。
- Lesson 11 正在学习，最小 Decision Eval 当前写在 `test.py`。
- `lesson_11_practice.py` 目前仍是 Lesson 10 AoT 练习的副本，不能视为 Lesson 11 已完成。
- Lesson 12 和最终综合项目尚未正式开始。

## 固定学习流程

```text
预测代码行为
  -> 阅读课程文档
  -> 找 complete_example.py 入口
  -> 追踪 Agent 方法和 helper
  -> 从零手敲最小练习
  -> 运行并观察中间数据
  -> 区分模型与 Python 的职责
  -> 记录失败模式和 Eval 用例
```

