from telegram import Update
from telegram.ext import ApplicationBuilder
from telegram.ext import MessageHandler
from telegram.ext import filters

import asyncio
from mcp import ClientSession
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
import  json
import ollama
import  re

async def get_token_from_mcp() -> str:

    params = StdioServerParameters(command="uv", args=["run", "ecommerce_server.py"])

    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:

            await session.initialize()

            res = await session.read_resource("resource://telegram_token_resource")
            try:
                return res.contents[0].text.strip()
            except Exception:
                return ""

def extract_tool_args(raw_text):

    clean_text = re.sub(r'//.*', '', raw_text)

    match = re.search(r'\{.*\}', clean_text, re.DOTALL)
    
    if not match:
        print(" لم يتم العثور على كائن JSON في النص.")
        return None, {}
    try:
        data = json.loads(match.group())
    
    except json.JSONDecodeError as e:
        print(f" فشل في تحليل JSON: {e}")
        return None, {}
    
    return data.get("tool"), data.get("args", {})

async def classify_and_execute(user_id: str, message: str) -> str:
    try:
        server_params = StdioServerParameters(command="uv", args=["run", "ecommerce_server.py"])

        async with stdio_client(server_params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()

                prompt = await session.get_prompt("ecommerce_prompt", {"user_input": message})

                prompt_text = prompt.messages[0].content.text

                response = ollama.chat(
                    model="llama3",
                    messages=[{"role": "system", "content": prompt_text}] 
                )

                raw = response["message"]["content"].strip()

                tool, args = extract_tool_args(raw.strip())

                if not tool:
                    msg= await session.read_resource("resource://custom_data_snippet_resource")
                    return msg
                args = (args or {})
                args["user_id"] = str(user_id)

                result = await session.call_tool(tool, args)

                return (result.content[0].text or "").strip()
            
    except Exception as e:
        return f"حدث خطأ أثناء تنفيذ الطلب:\n{e}"

async def handle_message(update: Update, context):
    try:
        if not update.message or not update.message.text:
            return
        
        user_text = update.message.text.strip()

        user_id = str(update.effective_user.id)

        reply = await classify_and_execute(user_id, user_text)
        await update.message.reply_text(str(reply) or "لم يصلني رد من الخدمة.")
    
    except Exception as e:
        return f"حدث خطأ أثناء تنفيذ الطلب:\n{e}"

async def main():
    try:

        token =  await get_token_from_mcp()
        if not token:
            raise RuntimeError("لم يتم العثور على TELEGRAM_TOKEN   ")

        app = ApplicationBuilder().token(token).build()

        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        await app.initialize()
        await app.start()
        print("🤖 البوت شغّال الآن… اضغط Ctrl+C للإيقاف.")

        await app.updater.start_polling()

        await asyncio.Event().wait()
    except asyncio.CancelledError:
        print("تمّ إيقاف البوت")

if __name__ == "__main__":
        asyncio.run(main())

