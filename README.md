# Envrionment Setup
* Make a file in the repository folder (right next to LICENSE) and name it ".env"
* Add to that file the line ```GEMINI_API_KEY=<your api key>```
  * Note that you can get your api key from Google AI Studio.
* Install UV using [official guide](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) or via ```pip install uv```.
* Navigate your terminal to repo folder and run command ```uv sync```
* You're all set!

> Beware Running this agent can eat up your api credits specially that it's not currently limited in terms of calls or steps.
