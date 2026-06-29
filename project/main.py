from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.getenv("API_KEY"))
app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), 'template'))
chat_response = []


@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(
        name="home.html",
        request=request,
        context={'chat_response': chat_response})

chat_log = [{'role': 'system',
             'content': 'you are  coding bot that responsible for answering  anything include programming.'}]


@app.websocket("/ws")
async def chat(websocket: WebSocket):

    await websocket.accept()

    while True:

        user_input = await websocket.receive_text()

        chat_log.append({
            "role": "user",
            "content": user_input
        })

        try:

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=chat_log,
                temperature=0.6,
                stream=True
            )

            ai_response = ""

            for chunk in response:

                if chunk.choices[0].delta.content:

                    token = chunk.choices[0].delta.content

                    ai_response += token

                    await websocket.send_text(token)

            chat_log.append({
                "role": "assistant",
                "content": ai_response
            })

            chat_response.append({
                "user": user_input,
                "bot": ai_response
            })

        except Exception as e:

            await websocket.send_text("Error: " + str(e))


@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):
    chat_log.append({'role': 'user', 'content': user_input})

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=chat_log,
        temperature=0.2)

    bot_response = response.choices[0].message.content
    chat_response.append({
        'user': user_input,
        'bot': bot_response
    })
    chat_log.append({'role': 'assistant', 'content': bot_response})

    return templates.TemplateResponse(
        request=request,
        name='home.html',
        context={'chat_response': chat_response}
    )


@app.get('/image', response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse(
        name="image.html",
         request= request,
         context={
            "image_url": None
        })



@app.post("/image", response_class=HTMLResponse)
async def create_image(
    request: Request,
    user_input: Annotated[str, Form()],
    size: Annotated[str, Form()],
    width: Annotated[int | None, Form()] = None,
    height: Annotated[int | None, Form()] = None,
):

    if size == "custom":
        size = f"{width}x{height}"

    response = client.images.generate(
        model="gpt-image-1",
        prompt=user_input,
        size=size,
    )

    image_url = response.data[0].b64_json

    return templates.TemplateResponse(
        name="image.html",
        request= request,
            context={"image_url": image_url,
        },
    )
