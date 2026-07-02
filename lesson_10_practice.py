import json
from llama_cpp import Llama

def  extract_json_from_text(text):
    start = text.find("{")


    if start == -1 :
        return None
    
    decoder = json.JSONDecoder()

    try:
        parsed, end = decoder.raw_decode(text[start:])
        return parsed
    except json.JSONDecodeError:
        return None
    

class LocalLLM:
    def __init__(self, model_path):
        self.llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            verbose=False,
        )

    def generate(self, prompt,temperature=None):
        kwargs = {
            "prompt":prompt,
            "max_tokens":128,
            "stop":["</s>", "\n\n", "User:", "Assistant:"],
        }

        if temperature is not None:
            kwargs["temperature"] = temperature

        response = self.llm(**kwargs)
        return response["choices"][0]["text"].strip()

def validate_graph(graph):
    if not graph:
        return False
    
    if"nodes" not in graph:
        return False
    
    if not isinstance(graph["nodes"],list):
        return False
    
    node_ids = set()

    # 第一次检查：节点结构及编号
    for node in graph["nodes"]:
        if not isinstance(node,dict):
            return False
        
        if "id" not in node:
            return False
        
        if "action" not in node:
            return False
        
        if "depends_on" not in node:
            return False
        
        if not isinstance(node["depends_on"],list):
            return False
        
        if node["id"] in node_ids:
            return False
        
        node_ids.add(node["id"])

    # 第二次检查：依赖编号是否真实存在
    for node in graph["nodes"]:
        for dependency in node["depends_on"]:
            if dependency not in node_ids:
                return False
            
    return True

def create_aot_graph(llm, goal):
    prompt = f"""Create an atomic execution graph for the goal.

Each node represents one action.
Dependencies must reference node IDs.

CRITICAL INSTRUCTIONS:
1. Respond with ONLY valid JSON
2. No explanations, no markdown, no other text
3. Start your response with {{ and end with }}

Required JSON format:
{{
  "nodes": [
    {{
      "id": "1",
      "action": "research",
      "depends_on": []
    }},
    {{
      "id": "2",
      "action": "write",
      "depends_on": ["1"]
    }}
  ]
}}

Each node must have:
- id: a unique string such as "1", "2", or "3"
- action: the action to perform
- depends_on: IDs that must finish first

Goal:
{goal}

Response (JSON only):"""
    
    for attempt in range(3):
        response = llm.generate(
            prompt,
            temperature=0.0,
        )

        print("raw graph response:", response)

        graph = extract_json_from_text(response)

        if validate_graph(graph):
            return graph
        
    return None

def execute_graph(graph,executor_func):
    if not validate_graph(graph):
        return []
    
    nodes = graph["nodes"]

    # 保存已经执行完成的节点编号
    executed = set()

    # 保存每个节点的执行结果
    results = []

    # 防止循环依赖造成无限循环
    max_iterations = len(nodes) * 2
    iteration = 0

    while (
        len(executed) < len(nodes)
        and iteration < max_iterations
    ):
        iteration = iteration + 1

        for node in nodes:
            node_id = node["id"]

            # 已经执行过的节点直接跳过
            if node_id in executed:
                continue

            dependencies = node.get(
                "depends_on",
                [],
            )

            # 检查全部依赖是否已经执行完成
            dependencies_ready = all(
                dependency in executed
                for dependency in dependencies
            )

            if dependencies_ready:
                try:
                    result = executor_func(
                        node["action"]
                    )

                    results.append({
                        "node_id": node_id,
                        "action": node["action"],
                        "result":result,
                        "success":True,
                    })

                    executed.add(node_id)

                except Exception as error:
                    results.append({
                        "node_id": node_id,
                        "action": node["action"],
                        "error": str(error),
                        "success": False,
                    })

                    executed.add(node_id)

    return results

class SimpleAgent:
    def __init__(self,model_path):
        self.llm = LocalLLM(model_path)

    def create_aot_plan(self,goal):
        return create_aot_graph(
            self.llm,
            goal,
        )
    
    def execute_aot_plan(self,graph):
        def execute_action(action):
            # 这里只是模拟执行，还没有调用真实工具
            return f"Executed: {action}"

        return execute_graph(
            graph,
            execute_action,
        )
    
agent = SimpleAgent(
    "models/llama-3-8b-instruct.gguf"
)

goal = "Research and write an article about AI agents"

# 第一次调用模型：生成带依赖关系的执行图
graph = agent.create_aot_plan(goal)

print("AoT graph:", graph)

if graph:
    # Python 根据依赖关系执行节点
    results = agent.execute_aot_plan(graph)

    print("execution results:")

    for index,result in enumerate(results,1):
        print(f"result {index}:",result)

else:
    print("graph generation failed.")


