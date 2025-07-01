from dotenv import load_dotenv

from ShoppingAgent import ShoppingAgent

load_dotenv()

shopping_agent = ShoppingAgent()
with open("graph2.png", "wb") as f:
    f.write(shopping_agent.get_graph().draw_mermaid_png())
print("Graph image saved as graph.png")

# user_msg = "i want to build a pc and my budget is 1000 USD"
user_msg = "i want an apartment in faisal street in giza egypt for rental. My budget is 10k EGP"
# user_msg = "hello, my name is ahmed"
while True:
    shopping_agent.test(user_msg)
    user_msg = str(input(": "))
