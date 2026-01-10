from dotenv import load_dotenv
load_dotenv()
import os
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.tools import Tool
from langchain_openai import ChatOpenAI
from langchain import hub
# Make sure your 'utils' folder exists!
from services.crypto_api import get_market_data
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn



# 1. Define the Tool
market_tool = Tool(
    name="CryptoMarketData",
    func=get_market_data,
    description="Useful for getting market reports. Input should be a symbol like 'BTC'."
)


# 2. Initialize Agent
def build_agent():
    # Pull the standard prompt from the Hub
    prompt = hub.pull("hwchase17/react")

    llm = ChatOpenAI(temperature=0.5, model="gpt-4o-mini")

    tools = [market_tool]

    agent = create_react_agent(llm, tools, prompt)

    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)


# 3. Server Setup
app = FastAPI()
agent_executor = build_agent()


class Query(BaseModel):
    q: str


@app.post("/query")
async def query_agent(query: Query):
    # --- THIS IS THE FIX ---
    # We create the prompt_text variable here so the next line can find it
    prompt_text = (
        f"Act as a Crypto Analyst. Analyze: {query.q}. "
        "Use the tool to get data. Summarize the trend."
    )
    # -----------------------

    response = agent_executor.invoke({"input": prompt_text})
    return {"result": response["output"]}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)