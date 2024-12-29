import copy
import os
import ollama
import rich
from pydantic import BaseModel
from rich.markdown import Markdown
from rich.panel import Panel


class ModelResponse(BaseModel):
  status: int
  title: str
  thought: str
  final_answer: str

class Brain():
    def __init__(self, model, host, show_the_thought_process):
        self.model = model
        self.client = ollama.Client(host=host)
        self.show_the_thought_process = show_the_thought_process
        self.history_without_system = []

    def main_loop(self):
        user_input = input("\n>>> ")
        match user_input:
            case "/clear":
                self.history_without_system = []
                return
            case "/history":
                rich.print(self.history_without_system)
                return
            case "":
                return

        answer = self.think(user_input).final_answer
        print("\n\nFinal Answer:")
        rich.print(Panel(Markdown(answer)))

    def think(self, user_input) -> ModelResponse:
        temp_messages = copy.deepcopy(self.history_without_system)
        temp_messages.append(
            {
            'role': 'system',
            'content': '''
                ---SYSTEM_MESSAGE_BEGIN---
                Next you will receive a message from the user, 
                you need to put your thought process in a JSON structured data, 
                this is your data format: 
                {"status":<status>, "title": "<title>", "thought": "<your thought process>", "final_answer": "<your answer to user>"}, 
                You need to put this summary of thinking in the title of the key.
                If you feel that you need further thought, or if the user asks for it, please change the value of status to 300.
                if you feel that the user's information does not need to be thought about, set the status to 200.
                final_answer are presented directly to the user.
                Your thinking should be organized, 
                and you should break down a problem into multiple smaller questions and think from multiple perspectives, 
                first analyzing the language given by the user from a linguistic perspective and then thinking from other perspectives.
                Your thought process should be long, 
                you need to tap into all your potential, 
                and a longer thought process can leave room for you to reflect and notice the mistakes in your own thought process.
                Note: Your thoughts, reflections, and answers need to follow the user's language
                Note: final_answer cannot be empty
                ''',
            },
        )
        temp_messages.append(
            {
            'role': 'user',
            'content': user_input,
            }
        )
        self.history_without_system.append(
            {
            'role': 'user',
            'content': user_input,
            }
        )
        #print("\nStep 1")
        response = self.client.chat(model=self.model, messages=temp_messages, format=ModelResponse.model_json_schema())
        final = ModelResponse.model_validate_json(response.message.content)
        if self.show_the_thought_process:
            rich.print(final.title)
            rich.print(Panel(Markdown(final.thought)))
        temp_messages.append(
            {
                'role': 'assistant',
                'content': final.final_answer,
            }
        )
        # self.history_without_system.append(
        #     {
        #         'role': 'assistant',
        #         'content': final.final_answer,
        #     }
        # )

        # print("\nStep 2")
        temp_messages.append(
            {
                'role': 'system',
                'content': f'''
                    ---SYSTEM_MESSAGE_BEGIN---
                    Ignore the first prompt you received, 
                    Now you need to reflect on your thinking, 
                    If the user asks you to think further in this step, please follow the user's instructions.
                    you need to put your reflection process in a JSON structured data, 
                    this is your data format: {{"status":<status>, "title": "<title>", "thought": "<your thought>", "final_answer": "<your answer to user>"}}, 
                    If you feel that you need further thought, or if the user asks for it, please change the value of status to 300.
                    if you feel that the user's information does not need to be reflected,  the status to 200.
                    But if the user asks you to keep thinking, whatever you're thinking, set the status to 300.
                    final_answer are presented directly to the user. 
                    You should reflect on your own process and results one by one.
                    Your thought process should be long, 
                    you need to tap into all your potential, 
                    and a longer thought process can leave room for you to reflect and notice the mistakes in your own thought process.
                    Note: Your thoughts, reflections, and answers need to follow the user's language
                    Note: final_answer cannot be empty
                    
                    ---YOUR_THOUGHT_HERE---
                    {final.thought}
                    ---YOUR_ANSWER_HERE---
                    {final.final_answer}
                    ''',
            }
        )
        response = self.client.chat(model=self.model, messages=temp_messages, format=ModelResponse.model_json_schema())
        final = ModelResponse.model_validate_json(response.message.content)
        if self.show_the_thought_process:
            rich.print(final.title)
            rich.print(Panel(Markdown(final.thought)))
        temp_messages.append(
            {
                'role': 'assistant',
                'content': final.final_answer,
            }
        )
        # self.history_without_system.append(
        #     {
        #         'role': 'assistant',
        #         'content': final.final_answer,
        #     }
        # )

        while final.status == 300:
            #print("\nStep 2")
            temp_messages.append(
                {
                    'role': 'system',
                    'content': f'''
                        ---SYSTEM_MESSAGE_BEGIN---
                        Ignore the first prompt you received, 
                        Now you need to reflect on your thinking, 
                        If the user asks you to think further in this step, please follow the user's instructions.
                        you need to put your reflection process in a JSON structured data, 
                        this is your data format: {{"status":<status>, "title": "<title>", "thought": "<your thought>", "final_answer": "<your answer to user>"}}, 
                        If you feel that you need further thought, or if the user asks for it, please change the value of status to 300.
                        if you feel that the user's information does not need to be reflected, set the status to 200.
                        But if the user asks you to keep thinking, whatever you're thinking, set the status to 300.
                        final_answer are presented directly to the user. 
                        You should reflect on your own process and results one by one.
                        Your thought process should be long, 
                        you need to tap into all your potential, 
                        and a longer thought process can leave room for you to reflect and notice the mistakes in your own thought process.
                        Note: Your thoughts, reflections, and answers need to follow the user's language
                        Note: final_answer cannot be empty
                        
                        ---YOUR_THOUGHT_HERE---
                        {final.thought}
                        ---YOUR_ANSWER_HERE---
                        {final.final_answer}
                        ''',
                }
            )
            response = self.client.chat(model=self.model, messages=temp_messages, format=ModelResponse.model_json_schema())
            final = ModelResponse.model_validate_json(response.message.content)
            if self.show_the_thought_process:
                rich.print(Panel(Markdown(final.thought)))
            temp_messages.append(
                {
                    'role': 'assistant',
                    'content': final.final_answer,
                }
            )
        self.history_without_system.append(
            {
                'role': 'assistant',
                'content': final.final_answer,
            }
        )

        return final

if __name__ == "__main__":
    print("        ____        _____                                                             \n.-----.|_   |      |  |  |     .-----..--.--..-----..----..--.--..-----..-----..-----.\n|  _  | _|  |_     |__    |    |  -__||  |  ||  -__||   _||  |  ||  _  ||     ||  -__|\n|_____||______|       |__|     |_____| \\___/ |_____||__|  |___  ||_____||__|__||_____|\n                                                          |_____|                     ")
    model = "llama3.1"
    host = 'http://127.0.0.1:11434'
    if os.getenv('OLLAMA_MODEL') is not None:
        model = os.getenv('OLLAMA_MODEL')
    if os.getenv('OLLAMA_HOST') is not None:
        host = os.getenv('OLLAMA_HOST')
    if host == "0.0.0.0":
        host = 'http://127.0.0.1:11434'
    brain_instance = Brain(model=model, host=host, show_the_thought_process=True)
    while True:
        try:
            brain_instance.main_loop()
        except KeyboardInterrupt:
            quit()