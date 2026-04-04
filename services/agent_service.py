import uuid

from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from utils.prompt import SYSTEM_PROMPT
from models.model import Context, ResponseFormat


class AgentService:
    def __init__(
        self,
        temperature: float = 0.3,
        model: str = "openai:gpt-5-mini",
        user_id: str = None,
    ):
        thread_id = user_id or str(uuid.uuid4())
        chat_model = init_chat_model(model, temperature=temperature)
        self.context = Context(user_id=thread_id)
        self.config = {"configurable": {"thread_id": thread_id}}
        self.agent = create_agent(
            model=chat_model,
            system_prompt=SYSTEM_PROMPT,
            context_schema=Context,
            response_format=ResponseFormat,
            checkpointer=InMemorySaver(),
        )

    def send_message(self, message: str) -> ResponseFormat:
        agent_input = {"messages": [{"role": "user", "content": message}]}
        return self.agent.invoke(
            agent_input,
            context=self.context,
            config=self.config,
        )["structured_response"]
