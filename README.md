# LLM-Telegram-Bot

Telegram bot for chatting with LLM models (Mixtral, LLama) via Groq Cloud.

<h2>How to use:</h2>

1. Start bot: https://t.me/ai_mait_llm_gpt_bot
2. Choose LLM (optionally): send /conf command
3. Start chatting
4. Enjoy!
5. Buy me a coffee if you like it ☕️❤️ https://www.buymeacoffee.com/aimate

<h2>How to set up your own Telegram bot:</h2>

If you want to customize the bot for your own needs here are the steps to set up your own LLM Telegram bot:
1. Create your Telegram bot with <a href="https://t.me/botfather">BotFather</a>
2. Get your bot API Token. Don't know how? <a href="https://core.telegram.org/bots/">Read the Telegram Bot Documentation</a>
3. Add your bot API Token as your environment variable:
```bash
$ export TELEGRAM_LLM_BOT_TOKEN="<YOUR_BOT_API_TOKEN>"
```
Replace 
<b><YOUR_BOT_API_TOKEN></b>
with your actual token acquired in step 2.

4. Create a folder for the bot (in this example it is ~/LLM-Telegram-Bot) and Clone this repository
```bash
$ mkdir ~/LLM-Telegram-Bot
$ cd ~/LLM-Telegram-Bot
$ git clone https://github.com/vitalikrupenka/LLM-Telegram-Bot
```

5. Install dependencies
```bash
$ pip install -r requirements.txt
```

6. Run app.py
```bash
$ python app.py
```

Now you can simply ask your Telegram bot anything right in the chat and get a response.

>Important: the bot will be available only while app.py is running and your computer is on.
>If you want the bot to be always available it's better to deploy app.py somewhere in the cloud, like Heroku, AWS, PythonAnywhere or other services of your choice.

7. Enjoy!
