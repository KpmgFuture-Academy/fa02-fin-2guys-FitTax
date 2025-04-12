"""
LangChain 에이전트 모듈
"""
from functools import partial
from typing import List, Dict, Any

# 올바른 임포트 경로
from langchain.agents import AgentType, initialize_agent
from langchain.tools.base import Tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI  # 이 임포트가 누락됨

from langchain_openai import ChatOpenAI


from tax_assistant.chatbot.prompts import TAX_ASSISTANT_PROMPT

class SimpleConversationMemory:
    """간단한 대화 메모리 구현"""
    
    def __init__(self, return_messages=True, memory_key="chat_history"):
        self.chat_history: List[HumanMessage | AIMessage] = []
        self.return_messages = return_messages
        self.memory_key = memory_key
    
    def load_memory_variables(self, inputs):
        """메모리 변수 로드"""
        return {self.memory_key: self.chat_history}
    
    def save_context(self, inputs, outputs):
        """컨텍스트 저장"""
        self.chat_history.append(HumanMessage(content=inputs.get("input", "")))
        self.chat_history.append(AIMessage(content=outputs.get("output", "")))
    
    def add_message(self, message, is_user=True):
        if is_user:
            self.chat_history.append(HumanMessage(content=message))
        else:
            self.chat_history.append(AIMessage(content=message))
    
    def get_messages(self):
        return self.chat_history
    
    def clear(self):
        """메모리 초기화"""
        self.chat_history = []

def create_tax_assistant_agent(api_key, tools, tax_period="2025년 1기 (1월~6월)"):
    """
    부가세 신고 챗봇 어시스턴트 에이전트 생성
    """
    # LLM 설정
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.2,
        openai_api_key=api_key
    )
    
    # 도구들을 LangChain 도구 형식으로 변환
    converted_tools = []
    for tool in tools:
        if callable(tool) and not hasattr(tool, 'name'):  # 함수 기반 도구인 경우
            # 기본 도구 속성 설정
            tool_name = tool.__name__
            tool_description = tool.__doc__ or "도구 설명이 없습니다."
            converted_tool = Tool(
                name=tool_name,
                func=tool,
                description=tool_description
            )
            converted_tools.append(converted_tool)
        else:  # 이미 Tool 형식이거나 클래스 기반인 경우
            converted_tools.append(tool)
    
    # 커스텀 메모리 사용 - SimpleConversationMemory로 통일
    #memory = SimpleConversationMemory(return_messages=True, memory_key="chat_history")
    from langchain.memory import ConversationBufferMemory
    memory = ConversationBufferMemory(return_messages=True, memory_key="chat_history")

    
    # 부분적으로 채워진 프롬프트 생성
    partial_prompt = TAX_ASSISTANT_PROMPT.partial(tax_period=tax_period)
    
    # 에이전트 생성
    agent = initialize_agent(
        converted_tools,
        llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        prompt=partial_prompt,
        handle_parsing_errors=True
    )
    
    return agent

class TaxAssistantSession:
    """
    세금 어시스턴트 세션 관리 클래스
    """
    def __init__(self):
        self.chat_history = []
        self.agent = None
        self.tax_period = "2025년 1기 (1월~6월)"
    
    def initialize_agent(self, api_key, tools):
        """
        에이전트 초기화
        
        Args:
            api_key: OpenAI API 키
            tools: 에이전트가 사용할 도구 목록
        """
        self.agent = create_tax_assistant_agent(api_key, tools, self.tax_period)
    
    def add_message(self, message, is_user=True):
        """
        대화 이력에 메시지 추가
        
        Args:
            message: 메시지 내용
            is_user: 사용자 메시지 여부
        """
        if is_user:
            self.chat_history.append(HumanMessage(content=message))
        else:
            self.chat_history.append(AIMessage(content=message))
    
    def get_response(self, user_input):
        """
        사용자 입력에 대한 응답 생성
        
        Args:
            user_input: 사용자 입력 메시지
            
        Returns:
            에이전트 응답
        """
        if not self.agent:
            return "API 키가 설정되지 않았습니다. 먼저 API 키를 입력해주세요."
        
        try:
            # 현재는 단순하게 input만 전달
            response = self.agent.run(user_input)
            
            # 대화 이력 업데이트
            self.add_message(user_input, is_user=True)
            self.add_message(response, is_user=False)
            
            return response
        except Exception as e:
            error_message = f"오류가 발생했습니다: {str(e)}"
            return error_message