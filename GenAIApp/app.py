import os
import sys
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# 1. Load environment variables (.env)
load_dotenv()

# 2. Define the Prompt Template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are an expert tutor in {topic}. Explain concepts clearly and concisely."),
    ("user", "{user_question}")
])

# 3. Initialize the Large Language Model
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7
)

# 4. Initialize the Output Parser
output_parser = StrOutputParser()

# 5. Build the LCEL Chain
chain = prompt_template | llm | output_parser

# 6. Interactive Command Line App
if __name__ == "__main__":
    print("==========================================")
    print("Welcome to the LangChain AI Tutor!")
    print("Type 'exit' or 'quit' at any prompt to stop.")
    print("==========================================")
    
    topic = input("\nEnter the topic you want to learn about (e.g., Python, Physics): ").strip()
    
    if topic.lower() in ["exit", "quit", ""]:
        print("Goodbye!")
        sys.exit()

    print(f"\nAwesome! Ask any question about {topic}.\n")
    
    while True:
        user_question = input("\nYour Question > ").strip()
        
        if user_question.lower() in ["exit", "quit"]:
            print("\nThanks for using the AI Tutor. Goodbye!")
            break
            
        if not user_question:
            continue

        print("\nAI Thinking...\n")
        print("AI Response: ", end="", flush=True)

        # 7. Stream the response token-by-token using .stream() instead of .invoke()
        for chunk in chain.stream({"topic": topic, "user_question": user_question}):
            print(chunk, end="", flush=True)
            
        print("\n" + "-" * 50)