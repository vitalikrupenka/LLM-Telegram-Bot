import json
import os
import boto3
from telebot import TeleBot, types
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import SimpleConversationMemory
from langchain_groq import ChatGroq

# DynamoDB initialization
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('TelegramBotUsers')

# Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# TeleBot initialization
bot = TeleBot(TELEGRAM_BOT_TOKEN)

# Define model choices
models = ['mixtral-8x7b-32768', 'llama2-70b-4096']
default_model = models[0]

# Helper Functions
def get_user_data(user_id):
    response = table.get_item(Key={'UserId': user_id})
    return response['Item'] if 'Item' in response else None

def update_user_data(user_id, data):
    table.put_item(Item={'UserId': user_id, **data})

def create_conversation(model):
    groq_chat = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=model)
    return ConversationChain(llm=groq_chat, memory=SimpleConversationMemory())

# Message Handlers
def handle_start(chat_id):
    welcome_message = (f"Welcome to AI Mate LLM Bot!\n\n"
                       f"The current model is set to {default_model}\n\n"
                       "Use the /conf command to change the model.\n\n"
                       "Feel free to ask anything. Let's talk!")
    bot.send_message(chat_id, welcome_message)

def handle_conf(chat_id):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for model in models:
        markup.add(types.KeyboardButton(model))
    bot.send_message(chat_id, "Choose the model for the conversation:", reply_markup=markup)

def handle_text(chat_id, text, user_id):
    user_data = get_user_data(user_id)
    model = user_data['model'] if user_data and 'model' in user_data else default_model
    conversation = create_conversation(model)
    response = conversation.process(text)
    bot.send_message(chat_id, response)
    # Update conversation history in DynamoDB
    history = user_data['chat_history'] if user_data and 'chat_history' in user_data else []
    history.append(text)
    history = history[-100:]  # Keep only the last 100 messages
    update_user_data(user_id, {'chat_history': history, 'model': model})

# AWS Lambda Handler
def lambda_handler(event, context):
    try:
        if 'body' in event:
            update = json.loads(event['body'])
            message = update['message']
            chat_id = message['chat']['id']
            text = message['text']
            user_id = str(chat_id)  # Telegram chat ID as user ID
            
            if text == '/start':
                handle_start(chat_id)
            elif text == '/conf':
                handle_conf(chat_id)
            else:
                handle_text(chat_id, text, user_id)
                
            return {'statusCode': 200, 'body': json.dumps('OK')}
        return {'statusCode': 400, 'body': json.dumps('No valid input found')}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps('Internal server error')}

