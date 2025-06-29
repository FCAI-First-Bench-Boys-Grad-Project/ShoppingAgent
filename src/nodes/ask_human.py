from langchain_core.messages import HumanMessage
from src.states.MainState import MainState as State


# Define the function that calls the model
def ask_human(state: State):
    print(state['messages'])
    user_message = ''
    cnt = 0
    while (user_message == '' and cnt < 3):
        user_message = input("Please provide your input: ")
        cnt += 1

    return {"messages": [HumanMessage(user_message)], "isHuman": True, "user_messages": [HumanMessage(user_message)]}
