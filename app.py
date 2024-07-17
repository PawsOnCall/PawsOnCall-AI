from flask import Flask, request, jsonify
from openai import OpenAI
import time

app = Flask(__name__)

api_key = "sk-proj-7CsNxqCHaQWrcK5BckoJT3BlbkFJ7XbwKi6zRqXBYtkTpH4i"
assistant_id = "asst_UapxTTuKSMGIicECa1MFni4P"

client = OpenAI(
    api_key=api_key,
)

def get_assistant_id(request):
    targer_assistant_id = request.headers.get('Assistant-Id')
    if targer_assistant_id is not None and targer_assistant_id.strip() != "":
        return targer_assistant_id
    else:
        return assistant_id

@app.errorhandler(Exception)
def handle_error(e):
    code = 500
    response = {
        "error": {"code": code, "message": "Internal Server Error", "details": str(e)}
    }
    return jsonify(response), code


@app.route("/chat", methods=["POST"])
def chat():
    thread_id = request.json.get("threadId")
    content = request.json.get("content")
    if thread_id is None or thread_id.strip() == "":
        thread = client.beta.threads.create()
        thread_id = thread.id

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=content,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=get_assistant_id(request),
    )
    while run.status != "completed":
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    last_message = next(
        (
            message
            for message in messages
            if message.run_id == run.id and message.role == "assistant"
        ),
        None,
    )

    return jsonify(
        {
            "threadId": last_message.thread_id,
            "answer": last_message.content[0].text.value,
            "raw": last_message.model_dump(),
        }
    )


@app.route("/assistants/instructions", methods=["PUT"])
def update_instructions():
    return client.beta.assistants.update(
        get_assistant_id(request),
        instructions=request.json.get("instructions"),
    ).model_dump()


@app.route("/files", methods=["POST"])
def upload_file():
    request_file = request.files["file"]
    file = client.files.create(file=(request_file.filename, request_file.read()), purpose="assistants")
    assistant_file = client.beta.assistants.files.create(
        assistant_id=get_assistant_id(request), file_id=file.id
    )
    return assistant_file.model_dump()


@app.route("/files/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    client.beta.assistants.files.delete(assistant_id=get_assistant_id(request), file_id=file_id)
    return client.files.delete(file_id).model_dump()


@app.route("/files", methods=["GET"])
def get_files():
    return [file.model_dump() for file in get_files(get_assistant_id(request))]


def get_files(assistant_id):
    return [
        client.files.retrieve(file.id)
        for file in client.beta.assistants.files.list(assistant_id=assistant_id)
    ]


if __name__ == "__main__":
    app.run(port=3000)
