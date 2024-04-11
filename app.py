import telebot
from telebot import types
import os
import logging
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq

# Set up logging
logging.basicConfig(level=logging.INFO)  # Set to INFO to reduce the amount of log output

# Initialize the bot with your Telegram Bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_LLM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Set up Groq client with LangChain
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
conversational_memory_length = 100
memory = ConversationBufferWindowMemory(k=conversational_memory_length)

# Initialize default model and conversation
default_model = "mixtral-8x7b-32768"  # Set the default model
groq_chat = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=default_model)
conversation = ConversationChain(llm=groq_chat, memory=memory)

# Define a dictionary to store user data and session state
user_data = dict()
session_state = {'chat_history': [], 'model': default_model, 'conversation': conversation}

# Define model choices
models = ['mixtral-8x7b-32768', 'llama2-70b-4096']  # Extend with other models

# Function to create the configuration inline keyboard for models
def create_model_inline_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    model_buttons = [types.InlineKeyboardButton(text=model, callback_data='model_' + model) for model in models]
    keyboard.add(*model_buttons)
    return keyboard

# Callback query handler to process inline keyboard responses for models
@bot.callback_query_handler(func=lambda call: call.data.startswith('model_'))
def handle_callback_query(call):
    model = call.data.split('_')[1]
    session_state['model'] = model
    # Update the conversation object to use the selected model
    groq_chat = ChatGroq(groq_api_key=GROQ_API_KEY, model_name=model)
    session_state['conversation'] = ConversationChain(llm=groq_chat, memory=memory)
    bot.answer_callback_query(call.id, f"Model set to {model}. You can now start chatting.\n\nLet's talk!")
    # Send a confirmation message
    bot.send_message(call.message.chat.id, f"The model has been set to {model}.\n\nLet's talk!")

# Start command handler
@bot.message_handler(commands=['start'])
def start(message):
    # Inform the user about the default model and how to change it
    bot.send_message(message.chat.id, f"Welcome to AI Mate LLM Bot!\n\nThe current model is set to {default_model}\n\nUse the /conf command to change the model.\n\nFeel free to ask anything. Let's talk!")

# Configuration command handler
@bot.message_handler(commands=['conf'])
def configuration(message):
    # Provide the model configuration options
    bot.send_message(message.chat.id, "Choose the model for the conversation:", reply_markup=create_model_inline_keyboard())

# Handle any incoming message
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Process the message using the current model in LLM (LangChain Language Model)
    response = process_message_and_respond(message.text)
    # Send the response back to the user as a new message
    bot.send_message(message.chat.id, response)

# Process text using LLM
def process_message_and_respond(text):
    # Use the current conversation object to process the text
    response = session_state['conversation'](text)
    # Append to chat history
    session_state["chat_history"].append({"human": text, "AI": response["response"]})
    # Return the response
    return response["response"]

# Start the bot
bot.polling()