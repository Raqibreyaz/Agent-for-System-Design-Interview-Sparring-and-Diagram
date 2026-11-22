import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from utils.tools import TOOLS, FUNCTION_NAME_TO_FUNCTION_MAP

load_dotenv()

client = OpenAI(
  base_url=os.getenv("BASE_URL"),
  api_key=os.getenv("API_KEY")
)

with open("conversation.json", "r") as f:
  messages = json.loads(f.read())

while(True):

  msg = input("You: ").strip()

  if not msg:
    continue
  
  if msg.lower() in ["bye", "exit", "goodbye"]:
    break

  messages.append({
    "role": "user",
    "content": msg
  })
  
  MAX_STEPS = 5
  for step in range(MAX_STEPS):
    
    res = client.chat.completions.create(
      model = os.getenv("MODEL"),
      messages = messages,
      tools = TOOLS
    )
    
    tool_calls = res.choices[0].message.tool_calls
    
    if not tool_calls:
      break
    
    messages.append({
      "role": "tool",
      "tool_calls": tool_calls
    })
    
    for tool_call in tool_calls:
      func_name = tool_call.function.name
      
      try:
        args = json.loads(tool_call.function.arguments)
        function = FUNCTION_NAME_TO_FUNCTION_MAP[func_name]
        output = function(**args)
      except Exception as e:
        output = f"Error while running {func_name}: {e}"

      messages.append({
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": json.dumps(output)
      })
  
  content = res.choices[0].message.content
  messages.append({
    "role": "assistant",
    "content": content
  })
  print(f"\nassistant: {content}")  
  
  with open("conversation.json", "w") as f:
      f.write(str(messages))
  