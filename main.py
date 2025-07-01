from dotenv import load_dotenv
import os
from ShoppingAgent import ShoppingAgent

RECURSION_LIMIT = 100
load_dotenv()
shopping_agent = ShoppingAgent()
with open("graph2.png", "wb") as f:
    f.write(shopping_agent.get_graph().draw_mermaid_png())
print("Graph image saved as graph.png")

# user_msg = "i want to build a pc and my budget is 1000 USD"
user_msg = "i want an apartment in faisal street in giza egypt for rental. My budget is 10k EGP"
# user_msg = "hello, my name is ahmed"
while True:
    for chunk in shopping_agent.ShoppingAgent.stream(
        {"messages": [
            {"role": "user", "content": user_msg}]
         },
        config={
            "recursion_limit": RECURSION_LIMIT,
            "configurable": {"thread_id": "1"}
        },
        stream_mode="updates"
    ):
        last_chunk = chunk
        thought_log = next(iter(chunk.values())).get('thoughts', "")
        # Update the placeholder with the growing log of thoughts
        print(chunk)
        print("\n")
    print(shopping_agent.run(user_msg))
    user_msg = str(input(": "))
