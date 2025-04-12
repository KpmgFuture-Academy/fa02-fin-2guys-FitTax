"""
LangChain 에이전트 모듈
"""
from functools import partial

from langchain.agents import AgentType, initialize_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

from tax_assistant.chatbot.prompts import TAX_ASSISTANT_PROMPT

def create_tax_assistant_agent(api_key, tools, tax_period="2025년 1기 (1월~6월)"):
    # LLM 설정
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.2,
        openai_api_key=api_key
    )
    
    # 메모리 생성
    memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")
    
    # 프롬프트 생성
    partial_prompt = TAX_ASSISTANT_PROMPT.partial(tax_period=tax_period)
    
    # 에이전트 생성
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        prompt=partial_prompt,
        handle_parsing_errors=True
    )
    
    return agent

class TaxAssistantSession:
    def __init__(self):
        self.chat_history = []
        self.agent = None
        self.tax_period = "2025년 1기 (1월~6월)"
    
    def initialize_agent(self, api_key, tools):
        self.agent = create_tax_assistant_agent(api_key, tools, self.tax_period)
    
    def add_message(self, message, is_user=True):
        if is_user:
            self.chat_history.append(HumanMessage(content=message))
        else:
            self.chat_history.append(AIMessage(content=message))
    
    def get_response(self, user_input):
        if not self.agent:
            return "API 키가 설정되지 않았습니다. 먼저 API 키를 입력해주세요."
        
        try:
            response = self.agent.run(user_input)
            self.add_message(user_input, is_user=True)
            self.add_message(response, is_user=False)
            return response
        except Exception as e:
            return f"오류가 발생했습니다: {str(e)}"