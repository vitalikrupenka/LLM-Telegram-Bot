import json
import os
import boto3
from telebot import TeleBot, types
import http.client

# DynamoDB initialization
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('TelegramBotUsers')

# Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = 'api.groq.com'
GROQ_API_RESOURCE = '/openai/v1/chat/completions'

# TeleBot initialization
bot = TeleBot(TELEGRAM_BOT_TOKEN)

# Telegram Mesage Types
telegram_message_types = [
    'text', 'audio', 'video', 'photo', 'voice', 'document',
    'sticker', 'video_note', 'contact', 'location', 'poll'
]

# Define model choices
models = ['mixtral-8x7b-32768', 'llama2-70b-4096']
default_model = models[0]

# Helper Functions
def get_user_data(user_id):
    response = None
    try:
        response = table.get_item(Key={'UserId': user_id})['Item']
    except Exception as e:
        print(str(e))
    return response

def update_user_data(user_id, data):
    table.put_item(Item={'UserId': user_id, **data})

def fetch_chat_completion(messages, model):
    conn = http.client.HTTPSConnection(GROQ_API_URL)
    payload = json.dumps({
        "messages": messages,
        "model": model
    })
    headers = {
      'Authorization': f'Bearer {GROQ_API_KEY}',
      'Content-Type': 'application/json'
    }
    conn.request("POST", GROQ_API_RESOURCE, payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))
     
    return json.loads(data.decode("utf-8"))['choices'][0]['message']['content']

# AWS Lambda Handlerfunction that handles the telegram bot core logic and processes messages based on their types.
def lambda_handler(event, context):
    try:
        update = json.loads(event['body'])
        
        # Handle callback queries from inline keyboards
        if 'callback_query' in update:
            handle_callback_query(update['callback_query'])
            return {'statusCode': 200, 'body': json.dumps('Callback query processed')}
        
        # Handle different types of messages
        elif 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']
            
            # Handling text messages
            if 'text' in message:
                text = message['text']
                if text.startswith('/'):
                    if text == '/start':
                        handle_start(chat_id)
                    elif text == '/conf':
                        handle_conf(chat_id)
                    elif text == '/menu':
                        handle_menu(chat_id)
                else:
                    user_id = str(chat_id)  # Telegram chat ID as user ID
                    handle_text(chat_id, text, user_id)
                return {'statusCode': 200, 'body': json.dumps('Text message processed')}

            # Handling audio messages
            elif 'audio' in message:
                handle_audio(chat_id, message['audio'])
                return {'statusCode': 200, 'body': json.dumps('Audio message processed')}

            # Handling video messages
            elif 'video' in message:
                handle_video(chat_id, message['video'])
                return {'statusCode': 200, 'body': json.dumps('Video message processed')}

            # Handling photo messages
            elif 'photo' in message:
                handle_photo(chat_id, message['photo'])
                return {'statusCode': 200, 'body': json.dumps('Photo message processed')}

            # Handling voice messages
            elif 'voice' in message:
                handle_voice(chat_id, message['voice'])
                return {'statusCode': 200, 'body': json.dumps('Voice message processed')}

            # Handling sticker messages
            elif 'sticker' in message:
                handle_sticker(chat_id, message['sticker'])
                return {'statusCode': 200, 'body': json.dumps('Sticker message processed')}

            # Handling document messages
            elif 'document' in message:
                handle_document(chat_id, message['document'])
                return {'statusCode': 200, 'body': json.dumps('Document message processed')}

            # Handling video_note messages
            elif 'video_note' in message:
                handle_video_note(chat_id, message['video_note'])
                return {'statusCode': 200, 'body': json.dumps('Video note message processed')}

            # Handling contact messages
            elif 'contact' in message:
                handle_contact(chat_id, message['contact'])
                return {'statusCode': 200, 'body': json.dumps('Contact message processed')}

            # Handling location messages
            elif 'location' in message:
                handle_location(chat_id, message['location'])
                return {'statusCode': 200, 'body': json.dumps('Location message processed')}

            # Handling poll messages
            elif 'poll' in message:
                handle_poll(chat_id, message['poll'])
                return {'statusCode': 200, 'body': json.dumps('Poll message processed')}

            else:
                # Send a message back to the user that the message type is unsupported
                bot.send_message(chat_id, f"Unsupported message type. Sorry, I can only process the following types of messages:\n\n{'\n'.join(telegram_message_types)}")
                return {'statusCode': 200, 'body': json.dumps('Unsupported message type')}
        
        print("Received an unexpected update structure:", update)
        bot.send_message(chat_id, "Sorry, something went wrong. Unexpected update structure received.")
        return {'statusCode': 400, 'body': json.dumps('No valid message or callback query found')}

    except Exception as e:
        print(f"Error handling the update: {str(e)}")
        bot.send_message(chat_id, "Sorry, something went wrong. Error handling the update.")
        return {'statusCode': 500, 'body': json.dumps('Internal server error')}

# Messaging handlers that interact with the user
def handle_start(chat_id):
    welcome_message = (f"Welcome to AI Mate LLM Bot!\n\n"
                       f"The current model is set to {default_model}\n\n"
                       "Use the /conf command to change the model.\n\n"
                       "Feel free to ask anything. Let's talk!")
    bot.send_message(chat_id, welcome_message, reply_markup=create_reply_keyboard())

def handle_conf(chat_id):
    markup = create_model_inline_keyboard()
    bot.send_message(chat_id, "Choose the model for the conversation:", reply_markup=markup)

def handle_summarize(chat_id):
    bot.send_message(chat_id, "Summarization feature is coming soon. Come back later.")

def handle_rewrite(chat_id):
    bot.send_message(chat_id, "Rewrite feature is coming soon. Come back later.")

def handle_menu(chat_id):
    markup = create_menu_inline_keyboad()
    bot.send_message(chat_id, "Choose a Quick Action:", reply_markup=markup)

def handle_callback_query(call):
    # Ensure that 'message' and 'from' are properly checked before access
    call_data = call.get('data')
    chat_id = call['message']['chat']['id']
    
    if call_data == 'conf':
        handle_conf(chat_id) 
    
    elif call_data == 'summarize':
        handle_summarize(chat_id)  
    
    elif call_data == 'rewrite':
        handle_rewrite(chat_id) 

    elif call_data == 'menu':
        handle_menu(chat_id)
    
    elif 'message' in call and 'from' in call:
        chat_id = call['message']['chat']['id']
        user_id = str(call['from']['id'])
        new_model = call['data'].split('model_')[1]

        # Fetch existing user data or initialize new
        user_data = get_user_data(user_id) or {}
        user_data['model'] = new_model  # Update model

        # Save updated user data to DynamoDB
        update_user_data(user_id, user_data)

        # Acknowledge the model change to the user
        bot.answer_callback_query(call['id'], "Model changed to " + new_model)
        bot.send_message(chat_id, "Model set to " + new_model + ". You can now continue the conversation.")
    else:
        print("Invalid callback query structure:", call)

def handle_text(chat_id, text, user_id):
    user_data = get_user_data(user_id)
    model = user_data['model'] if user_data and 'model' in user_data else default_model
    history = user_data['chat_history'] if user_data and 'chat_history' in user_data else []

    # Filter only user messages for context
    user_messages = [msg for msg in history if msg['role'] == 'user']

    # Append user's current message to the conversation history
    user_message = {"role": "user", "content": text}

    # Define system message for context
    system_message = {"role": "system", "content": "you are a helpful assistant."}
    messages = [system_message]

    # Add user messages for context, taking the last 100 user messages if there are more than 100
    context_frame = 10
    messages.extend(user_messages[-context_frame:] if len(user_messages) > context_frame else user_messages)

    # Add the current user message
    messages.append(user_message)

    # Fetch chat completion from LLM
    response = fetch_chat_completion(messages, model)
    
    # Append LLM response to the messages list for local context
    ai_response = {"role": "AI", "content": response}
    messages.append(ai_response)

    # Send the response to the user
    bot.send_message(chat_id, response, reply_markup=create_reply_keyboard())

    # Update conversation history in DynamoDB with both user and AI messages
    updated_history = history + [user_message, ai_response]
    updated_history = updated_history[-200:]  # Keep only the last 200 entries (100 user messages and their responses)
    update_user_data(user_id, {'chat_history': updated_history, 'model': model})

# Handler function for voice messages
def handle_voice(chat_id, voice_message):
    # TODO: Implement logic for handling voice messages here
    response_message = "Received a voice message with duration {} seconds.".format(voice_message['duration'])
    bot.send_message(chat_id, response_message)

# Handling audio messages
def handle_audio(chat_id, audio_message):
    # TODO: Implement logic for handling audio messages here
    response_message = "Received an audio message with duration {} seconds.".format(audio_message['duration'])
    bot.send_message(chat_id, response_message)    

# Handling video messages
def handle_video(chat_id, video_message):
    # TODO: Implement logic for handling video messages here
    response_message = "Received a video message with duration {} seconds.".format(video_message['duration'])
    bot.send_message(chat_id, response_message)    

# Handling photo messages
def handle_photo(chat_id, photo_message):
    # TODO: Implement logic for handling photo messages here
    response_message = "Received a photo message."
    bot.send_message(chat_id, response_message)    

# Handling sticker messages
def handle_sticker(chat_id, sticker_message):
    # TODO: Implement logic for handling sticker messages here
    response_message = "Received a sticker message."
    bot.send_message(chat_id, response_message)    

# Handling document messages
def handle_document(chat_id, document_message):
    # TODO: Implement logic for handling document messages here
    response_message = "Received a document message."
    bot.send_message(chat_id, response_message)    

# Handling video_note messages
def handle_video_note(chat_id, video_note_message):
    # TODO: Implement logic for handling video_note messages here
    response_message = "Received a video_note message."
    bot.send_message(chat_id, response_message)    

# Handling contact messages
def handle_contact(chat_id, contact_message):
    # TODO: Implement logic for handling contact messages here
    response_message = "Received a contact message."
    bot.send_message(chat_id, response_message)    

# Handling location messages
def handle_location(chat_id, location_message):
    # TODO: Implement logic for handling location messages here
    response_message = "Received a location message."
    bot.send_message(chat_id, response_message)    
 
# Handling poll messages
def handle_poll(chat_id, poll_message):
    # TODO: Implement logic for handling poll messages here
    response_message = "Received a poll message."
    bot.send_message(chat_id, response_message)    
   
# Create the configuration inline keyboard for models
def create_model_inline_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    model_buttons = [types.InlineKeyboardButton(text=model, callback_data='model_' + model) for model in models]
    keyboard.add(*model_buttons)
    keyboard.add(types.InlineKeyboardButton(text="Buy me a coffee", url="https://t.me/ai_mait_llm_gpt_bot/support"))
    return keyboard

def create_menu_inline_keyboad():
    buttons = [
        types.InlineKeyboardButton("Summarize (Coming Soon...)", callback_data='summarize'),
        types.InlineKeyboardButton("Rewrite (Coming Soon...)", callback_data='rewrite'),
        types.InlineKeyboardButton("Change LLM", callback_data='conf'),
        types.InlineKeyboardButton("Buy me a coffee", url="https://t.me/ai_mait_llm_gpt_bot/support")
    ]

    markup = types.InlineKeyboardMarkup()
    
    for button in buttons:
        markup.add(button)

    return markup

def create_reply_keyboard():
    try:
        types.ReplyKeyboardRemove()
    except Exception as e:
        print(f"Error creating Reply Keyboard: {str(e)}")
    
    buttons = [
        # types.KeyboardButton('/conf'),
        types.KeyboardButton('What you can do?'),
        types.KeyboardButton('Tell me a joke')
    ]

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False).row(*buttons)

    return keyboard