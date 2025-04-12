from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from db_prompt_loader import load_prompt_by_stage

def ask_question_from_db(stage, user_input, prev_question):
    template = load_prompt_by_stage(stage)
    prompt = PromptTemplate(input_variables=["user_input", "prev_question"], template=template)
    llm = ChatOpenAI(temperature=0.3)
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run({"user_input": user_input, "prev_question": prev_question})