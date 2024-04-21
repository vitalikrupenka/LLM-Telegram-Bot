import json
import os
import boto3
from telebot import TeleBot, types
import http.client

# Initialize DynamoDB and TeleBot
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('TelegramBotUsers')
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = 'api.groq.com'
GROQ_API_RESOURCE = '/openai/v1/chat/completions'
bot = TeleBot(TELEGRAM_BOT_TOKEN)

# Message types and model choices
telegram_message_types = [
    'text', 'audio', 'video', 'photo', 'voice', 'document', 'sticker', 'video_note', 'contact', 'location', 'poll'
]
models = ['mixtral-8x7b-32768', 'llama3-70b-8192', 'llama3-8b-8192', 'llama2-70b-4096']
labels = ['Fast + Memory, 32K: ', 'Smart but Slow, 8K: ', 'Fast Llama 3, 8K: ', 'Fast Llama 2, 4K: ']
default_model = models[0]

# Helper functions
def get_user_data(user_id):
    try:
        return table.get_item(Key={'UserId': user_id})['Item']
    except Exception as e:
        print(str(e))
        return None

def update_user_data(user_id, data):
    table.put_item(Item={'UserId': user_id, **data})

def fetch_chat_completion(messages, model):
    conn = http.client.HTTPSConnection(GROQ_API_URL)
    payload = json.dumps({"messages": messages, "model": model})
    headers = {'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'}
    conn.request("POST", GROQ_API_RESOURCE, payload, headers)
    data = conn.getresponse().read()
    return json.loads(data.decode("utf-8"))['choices'][0]['message']['content']

# AWS Lambda Handler
def lambda_handler(event, context):
    try:
        update = json.loads(event['body'])

        if 'callback_query' in update:
            handle_callback_query(update['callback_query'])
            return {'statusCode': 200, 'body': json.dumps('Callback query processed')}

        elif 'message' in update:
            chat_id = update['message']['chat']['id']
            handle_message(chat_id, update['message'])
            return {'statusCode': 200, 'body': json.dumps('Message processed')}

        print("Received an unexpected update structure:", update)
        bot.send_message(chat_id, "Sorry, something went wrong. Unexpected update structure received.")
        return {'statusCode': 400, 'body': json.dumps('No valid message or callback query found')}

    except Exception as e:
        print(f"Error handling the update: {str(e)}")
        bot.send_message(chat_id, "Sorry, something went wrong. Error handling the update.")
        return {'statusCode': 500, 'body': json.dumps('Internal server error')}

# Messaging handlers
def handle_message(chat_id, message):
    if 'text' in message:
        if message['text'].startswith('/'):
            handle_command(chat_id, message['text'])
        else:
            handle_text(chat_id, message['text'])
    else:
        handle_non_text_message(chat_id, message)

def handle_command(chat_id, command):
    if command == '/start':
        handle_start(chat_id)
    elif command == '/conf':
        handle_conf(chat_id)
    elif command == '/menu':
        handle_menu(chat_id)

def handle_text(chat_id, text):
    user_id = str(chat_id)
    user_data = get_user_data(user_id)
    model = user_data['model'] if user_data and 'model' in user_data else default_model
    history = user_data['chat_history'] if user_data and 'chat_history' in user_data else []

    user_messages = [msg for msg in history if msg['role'] == 'user']
    user_message = {"role": "user", "content": text}
    system_message = {"role": "system", "content": "you are a helpful assistant."}

    context_frame = 10
    messages = [system_message]
    messages.extend(user_messages[-context_frame:] if len(user_messages) > context_frame else user_messages)
    messages.append(user_message)

    response = fetch_chat_completion(messages, model)
    ai_response = {"role": "AI", "content": response}
    messages.append(ai_response)

    bot.send_message(chat_id, response, reply_markup=create_reply_keyboard())

    updated_history = history + [user_message, ai_response]
    updated_history = updated_history[-200:]
    update_user_data(user_id, {'chat_history': updated_history, 'model': model})

def handle_non_text_message(chat_id, message):
    # Message handling based on the message type from telegram_message_types
    message_type = next((t for t in telegram_message_types if t in message), None)
    if message_type:
        globals()[f"handle_{message_type}"](chat_id, message)
    else:
        bot.send_message(chat_id, f"Received an unsupported message type: {message}")
    
# Handler functions for various message types
handle_message_types = {
    key: 
        lambda chat_id, message, t=key: 
            bot.send_message(
                chat_id, 
                f"Received a {t} message: {message['message_id']}"
            ) 
    for key in telegram_message_types[1:]
}

# Handling other message types goes here
for message_type in handle_message_types:
    globals()[f"handle_{message_type}"] = handle_message_types[message_type]

# Utility functions for keyboard creation
def create_model_inline_keyboard():
    names = {model: label + model for model, label in zip(models, labels)}
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    model_buttons = [types.InlineKeyboardButton(text=label, callback_data='model_' + model) for model, label in names.items()]
    keyboard.add(*model_buttons)
    keyboard.add(types.InlineKeyboardButton(text="Buy me a coffee", url="https://t.me/ai_mait_llm_gpt_bot/support"))
    return keyboard

def create_menu_inline_keyboad():
    buttons = [
        types.InlineKeyboardButton("💁 Summarize (Coming Soon...)", callback_data='summarize'),
        types.InlineKeyboardButton("📝 Rewrite (Coming Soon...)", callback_data='rewrite'),
        types.InlineKeyboardButton("⚙️ Change LLM", callback_data='conf'),
        types.InlineKeyboardButton("☕️ Buy me a coffee", url="https://t.me/ai_mait_llm_gpt_bot/support")
    ]

    markup = types.InlineKeyboardMarkup()

    for button in buttons:
        markup.add(button)
    return markup

def create_reply_keyboard():
    buttons = [
        types.KeyboardButton('❓ What you can do?'),
        types.KeyboardButton('😂 Tell me a joke')
    ]

    return types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False).row(*buttons)

def handle_callback_query(call):
    call_data, chat_id = call.get('data'), call['message']['chat']['id']
    
    if 'model' in call_data:
        handle_change_model(chat_id, call_data.split('model_')[1], call['id'])
    elif call_data == 'summarize' or call_data == 'rewrite':
        bot.send_message(chat_id, f"{call_data.capitalize()} feature is coming soon. Come back later.")
    elif call_data == 'conf':
        handle_conf(chat_id)
    else:
        print("Invalid callback query structure:", call)

def handle_change_model(chat_id, new_model, call_id):
    user_id = str(chat_id)
    user_data = get_user_data(user_id)
    user_data['model'] = new_model
    update_user_data(user_id, user_data)
    bot.answer_callback_query(call_id, f"Model changed to {new_model}")
    bot.send_message(chat_id, f"Model set to {new_model}. You can now continue the conversation.")

# Initialization functions
def handle_start(chat_id):
    bot.send_message(chat_id, (
            "Welcome to AI Mate LLM Bot!\n\n"
            f"The current model is set to {default_model}\n\n"
            "Use the /conf command to change the model.\n\n"
            "Feel free to ask anything. Let's talk!"
    ), reply_markup=create_reply_keyboard())

def handle_conf(chat_id):
    bot.send_message(chat_id, "Choose the model for the conversation:", reply_markup=create_model_inline_keyboard())

def handle_menu(chat_id):
    bot.send_message(chat_id, "Choose a Quick Action:", reply_markup=create_menu_inline_keyboad())