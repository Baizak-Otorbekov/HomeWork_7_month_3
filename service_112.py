import sqlite3
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

ADMIN_USER_ID = 6267512015

qa_dict = {}

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_USER_ID

def create_db():
    conn = sqlite3.connect("qa_database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_question_to_db(question, answer):
    conn = sqlite3.connect("qa_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO qa (question, answer) VALUES (?, ?)", (question, answer))
    conn.commit()
    conn.close()

def delete_question_from_db(question):
    conn = sqlite3.connect("qa_database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM qa WHERE question = ?", (question,))
    conn.commit()
    conn.close()

def get_all_questions_from_db():
    conn = sqlite3.connect("qa_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM qa")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

async def start(update: Update, context: CallbackContext) -> None:
    first_name = update.message.from_user.first_name
    await update.message.reply_text(f"Здравствуйте, {first_name}! Я бот службы 112. Задайте ваш вопрос.")

def find_similar_questions(user_input: str) -> list:
    user_input_lower = user_input.lower()
    user_words = set(user_input_lower.split()) 
    suggestions = []
    
    for question in qa_dict:
        question_lower = question.lower()
        question_words = set(question_lower.split())  
        common_words = user_words.intersection(question_words)  

        if common_words:  
            suggestions.append((question, common_words))

    return suggestions

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_text = update.message.text.strip()

    response = qa_dict.get(user_text.lower(), None)
    if response:
        await update.message.reply_text(response)
    else:
        suggestions = find_similar_questions(user_text)
        if suggestions:
            suggestions = sorted(suggestions, key=lambda x: len(x[1]), reverse=True)
            message = "Я нашел похожие вопросы:\n" + "\n".join([q[0] for q in suggestions]) + "\n\nПожалуйста, выберите один из них."
            await update.message.reply_text(message)
        else:
            await update.message.reply_text("Извините, я не понял ваш вопрос. Попробуйте задать его по-другому.")

async def add_question(update: Update, context: CallbackContext) -> None:
    if is_admin(update.message.from_user.id):  
        try:
            if len(context.args) < 2:
                await update.message.reply_text("Ошибка: необходимо ввести вопрос и ответ. Формат: /addquestion <вопрос> <ответ>")
                return

            full_text = " ".join(context.args)
            if "или" in full_text:
                question, answer = full_text.split("или", 1)
            else:
                question = full_text
                answer = "Ответ не задан"

            question = question.strip()
            answer = answer.strip()

            if not question or not answer:
                await update.message.reply_text("Ошибка: вопрос или ответ не могут быть пустыми.")
                return

            add_question_to_db(question, answer)
            qa_dict[question] = answer
            await update.message.reply_text(f"Вопрос и ответ успешно добавлены:\n\nВопрос: {question}\nОтвет: {answer}")
        except IndexError:
            await update.message.reply_text("Ошибка: необходимо ввести вопрос и ответ. Формат: /addquestion <вопрос> <ответ>.")
    else:
        await update.message.reply_text("У вас нет прав для добавления вопросов и ответов.")

async def delete_question(update: Update, context: CallbackContext) -> None:
    if is_admin(update.message.from_user.id):
        try:
            if len(context.args) < 1:
                await update.message.reply_text("Ошибка: необходимо ввести вопрос для удаления. Формат: /deletequestion <вопрос>")
                return

            question = " ".join(context.args).strip()

            if question not in qa_dict:
                await update.message.reply_text("Ошибка: данный вопрос не найден в базе данных.")
                return

            delete_question_from_db(question)
            del qa_dict[question]  
            await update.message.reply_text(f"Вопрос успешно удален:\n\nВопрос: {question}")
        except IndexError:
            await update.message.reply_text("Ошибка: необходимо ввести вопрос для удаления. Формат: /deletequestion <вопрос>.")
    else:
        await update.message.reply_text("У вас нет прав для удаления вопросов.")

def main() -> None:
    create_db()  
    global qa_dict
    qa_dict = get_all_questions_from_db() 

    application = Application.builder().token('7839860873:AAG1ZxX5j-hZP4Sdj3l-vBdQdqAt6ZhKt5M').build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CommandHandler("addquestion", add_question))  
    application.add_handler(CommandHandler("deletequestion", delete_question))  # Добавлена команда для удаления

    print(">>> Бот запущен и ожидает сообщений")
    application.run_polling()

if __name__ == "__main__":
    main()