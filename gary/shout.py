import abc
from typing import TypedDict, Optional
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AbstractConversionAgent(abc.ABC):
    @abc.abstractmethod
    def input(self, data: str) -> None:
        pass
    @abc.abstractmethod
    def output(self) -> str:
        pass
    def build_chain(self, prompt):
        return prompt | self.llm | StrOutputParser()

class ConversionState(TypedDict):
    input_text: str      
    draft: str           
    final: str           

class SummaryTranslateView:
    def review(self, draft: str) -> str:
        print("\n** Intermediate Translation **")
        print(draft)
        user_input = input("Modify translation if needed, or press Enter to accept it: ")
        return user_input.strip() if user_input.strip() else draft

class SummaryTranslateAgent(AbstractConversionAgent):
    def __init__(self, target_language: str = "French", view: Optional[SummaryTranslateView] = None):
        self.target_language = target_language
        self.view = view or SummaryTranslateView()
        self.llm = ChatOpenAI(temperature=0)
        # Prompt for initial translation
        sys_msg = SystemMessagePromptTemplate.from_template(
            f"You are a translator. Translate the given text into {self.target_language}."
        )
        human_msg = HumanMessagePromptTemplate.from_template("{text}")
        self.initial_prompt = ChatPromptTemplate.from_messages([sys_msg, human_msg])
        self.initial_chain = self.build_chain(self.initial_prompt)
        # Prompt for final polishing
        final_sys = SystemMessagePromptTemplate.from_template(
            "You are to CAPITALIZE the given text."
        )
        final_human_template = (
            f"{{draft_text}}"

        )
        final_human = HumanMessagePromptTemplate.from_template(final_human_template)
        self.final_prompt = ChatPromptTemplate.from_messages([final_sys, final_human])
        self.final_chain = self.build_chain(self.final_prompt)
        self._build_graph()

    def _build_graph(self):
        builder = StateGraph(ConversionState)
        # First node: generate the draft translation.
        def initial_llm_node(state: ConversionState) -> dict:
            source = state["input_text"]
            draft = self.initial_chain.invoke({"text": source})
            return {"draft": draft}
        # Human review node: call interrupt.
        def review_node(state: ConversionState) -> dict:
            # This call triggers an interrupt on the first run.
            # When resumed, interrupt returns the human-provided value.
            user_input = interrupt({"text_to_revise": state["draft"]})
            return {"draft": user_input}
        # Final node: polish the translation.
        def final_llm_node(state: ConversionState) -> dict:
            draft = state["draft"]
            final = self.final_chain.invoke({"draft_text": draft})
            return {"final": final}
        builder.add_node("initial_llm", initial_llm_node)
        builder.add_node("human_review", review_node)
        builder.add_node("final_llm", final_llm_node)
        builder.add_edge(START, "initial_llm")
        builder.add_edge("initial_llm", "human_review")
        builder.add_edge("human_review", "final_llm")
        builder.add_edge("final_llm", END)
        self.graph = builder.compile(checkpointer=MemorySaver())

    def input(self, data: str) -> None:
        self._input_text = data

    def output(self) -> str:
        if not hasattr(self, "_input_text"):
            raise ValueError("Input not provided.")
        initial_state = {"input_text": self._input_text}
        thread_config = {"configurable": {"thread_id": "conv-agent-1"}}
        
        # Use streaming mode to catch the interrupt event.
        stream = self.graph.stream(initial_state, config=thread_config)
        for event in stream:
            if isinstance(event, dict) and "__interrupt__" in event:
                # Instead of extracting from event["__interrupt__"], just use the current state.
                state = self.graph.get_state(thread_config).values
                draft_text = state.get("draft", "")
                print("\n*** Graph paused for human review ***")
                user_edited = self.view.review(draft_text)
                resume_command = Command(resume=user_edited)
                self.graph.invoke(resume_command, config=thread_config)
                break

        final_state = self.graph.get_state(thread_config).values
        return final_state.get("final")



# --- Example usage ---
agent = SummaryTranslateAgent(target_language="French")
agent.input("Hello world! This is a test of the translation agent.")
result = agent.output()
print("\n=== Final Translation ===")
print(result)
