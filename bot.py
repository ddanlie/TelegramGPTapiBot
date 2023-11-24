from telegram import Update, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackContext, CallbackQueryHandler
from telegram.ext import filters

from openai import OpenAI



import re


class GptAi:

    
    SYSTEM_CONTENT = "Ты бот-ассистент в групповом чате, отвечай на вопросы пользователей небольшими сообщениями в 30-40 слов"
    MODEL = "gpt-3.5-turbo-1106"
    INPUT_PRICE = 0.000001 # $ for token
    OUTPUT_PRICE = 0.000002
    MAX_OUTPUT_TOKENS = 150
    PRICE_FILE = "price.txt"

    def __init__(self) -> None:
        self.default_price = GptAi.INPUT_PRICE * len(GptAi.SYSTEM_CONTENT.split(" "))
        self.client = OpenAI(api_key="")

    def read_price(self) -> float:
        with open(GptAi.PRICE_FILE, 'r') as file:
            p = float(file.read().strip())
        return p

    def count_price(self, prompt_cnt: int, complet_cnt: int) -> float:
        return self.default_price + GptAi.INPUT_PRICE * prompt_cnt + GptAi.OUTPUT_PRICE * complet_cnt

    def add_to_price(self, increase: float):

        price = self.read_price()

        with open(GptAi.PRICE_FILE, 'w') as file:
            file.write(str(round(price+increase, 5)))

        
    def get_answer(self, question) -> str:

        answer = ""
        try:
            completion =  self.client.chat.completions.create(
            model=GptAi.MODEL,
            messages=[ 
                {"role": "system", "content": GptAi.SYSTEM_CONTENT},
                {"role": "user", "content": question}
            ],
            max_tokens=GptAi.MAX_OUTPUT_TOKENS
            )
            answer = completion.choices[0].message.content

            self.add_to_price(self.count_price(completion.usage.prompt_tokens, completion.usage.completion_tokens))

        except Exception as e:
            print(e)

        return answer


class AiBot:


    ADDRESSING_PATTERN = r'^[Бб]от[,\s]' 
    HELP_COMMAND = "/help"
    HELP_TEXT = "Привет, я GPT бот. Чтобы получить от меня ответ обратись ко мне: 'Бот, <<вопрос>>'"
    PRICE_COMMAND = "/price"

    def __init__(self, token) -> None:

        self.application = Application.builder().token(token).build()
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.talk_handle))
        self.application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.new_group))
        self.application.add_handler(MessageHandler(filters.COMMAND, self.command))

        self.ai = GptAi()

        #self.users_limits = []
        self.allowed_groups = [-1001800504015]


    def start(self):
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


    async def new_group(self, update: Update, context: CallbackContext):
        id = update.message.chat_id
        if(id not in self.allowed_groups):
            await context.bot.leave_chat(id)

    async def command(self, update: Update, context: CallbackContext):
        if(update.message.text == AiBot.HELP_COMMAND):
            await context.bot.send_message(update.message.chat_id, AiBot.HELP_TEXT)

        if(update.message.text == AiBot.PRICE_COMMAND):
            await context.bot.send_message(update.message.chat_id, str(self.ai.read_price())+"$")


    async def  talk_handle(self, update: Update, context: CallbackContext):
        if re.match(AiBot.ADDRESSING_PATTERN, update.message.text) is None:
            return
        
        question = re.sub(AiBot.ADDRESSING_PATTERN, "", update.message.text)

        ans = self.ai.get_answer(question)

        await update.message.reply_text(ans)




if __name__ == "__main__":
    bot = AiBot("")
    bot.start()



