# Envrionment Setup
* Make a file in the repository folder (right next to LICENSE) and name it ".env"
* Add to that file the line ```GEMINI_API_KEY=<your api key>```
  * Note that you can get your api key from Google AI Studio.
* Add to that file the line ```LANGCHAIN_TRACING_V2=true```
* Add to that file the line ```LANGSMITH_ENDPOINT="https://api.smith.langchain.com"```
* Add to that file the line ```LANGSMITH_API_KEY=<your api key>```
  * Note that you can get your api key from LangSmith.
* Add to that file the line ```LANGSMITH_PROJECT="ShoppingAgent"```
  * The project name has to match the project name on LangSmith.
* Add to that file the line ```TAVILY_API_KEY=<your api key>```
  * Note that you can get your api key Tavily.
* Install UV using [official guide](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) or via ```pip install uv```.
* Navigate your terminal to repo folder and run command ```uv sync```
* You're all set!

> Beware Running this agent can eat up your api credits specially that it's not currently limited in terms of calls or steps.
