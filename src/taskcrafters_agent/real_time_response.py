import os
import requests
from langchain_community.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_community.tools import TavilySearchResults
from dotenv import load_dotenv
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import YouTubeSearchTool

load_dotenv()

llm = ChatOpenAI(
    model=os.environ.get("MODEL"),
    openai_api_base= os.environ.get("NEBIUS_BASE_URL"),
    openai_api_key=os.environ.get("NEBIUS_API_KEY"),
    temperature=0.2,
    streaming=True 
)

def get_location_from_ip(ip_address):
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        if response.status_code == 200:
            data = response.json()
            location = {
                "city": data.get("city", "Unknown"),
                "region": data.get("region", "Unknown"),
                "country": data.get("country", "Unknown")
            }
            return location
        else:
            return {"city": "Unknown", "region": "Unknown", "country": "Unknown"}
    except Exception as e:
        return {"city": "Unknown", "region": "Unknown", "country": "Unknown"}

def get_user_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json")
        if response.status_code == 200:
            data = response.json()
            return data.get("ip", "Unknown")
        else:
            return "Unknown"
    except Exception as e:
        return "Unknown"

ip_location_tool = Tool(
    name="IP Location Lookup",
    func=lambda ip: get_location_from_ip(ip),
    description="Useful for retrieving the geographical location of an IP address."
)

search_tool = TavilySearchResults()
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
duckduckgo = DuckDuckGoSearchRun()
youtube_search = YouTubeSearchTool()

tools = [
    Tool(
        name="Tavily Search", 
        func=search_tool.run,
        description="Useful for answering questions about current events, weather, flight information, or other real-time data."
    ),
    Tool(
        name="Wikipedia",
        func=wikipedia.run,
        description="Useful for answering general knowledge questions, definitions, and summaries about topics."
    ),
    Tool(
        name="DuckDuckGo Search",
        func=duckduckgo.run,
        description="Useful for searching the web for general information and alternative sources."
    ),
    Tool(
        name="YouTube Search",
        func=youtube_search.run,
        description="Useful for finding videos related to tutorials, reviews, or entertainment."
    ),
    ip_location_tool 
]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,  
    verbose=True,
    handle_parsing_errors=True,
)

def refine_instruction(instruction):
    location = get_location_from_ip(get_user_ip())
    city = location.get("city", "casablanca")
    
    if "weather" in instruction.lower():
        refinement_prompt = f"Refine the following instruction into a concise and effective query, including the location ({city}): {instruction}"
    else:
        refinement_prompt = f"Refine the following instruction into a concise and effective query: {instruction}"
    
    refined_instruction = llm.invoke(refinement_prompt).content 
    return refined_instruction.strip()

def validate_response(response, instruction):
    validation_prompt = (
        f"Validate the following response for relevance, safety, and accuracy. "
        f"If it is irrelevant, unsafe, or inaccurate, rewrite it to be appropriate. "
        f"Original Response: {response}\n"
        f"User Instruction: {instruction}"
    )
    validated_response = llm.invoke(validation_prompt).content
    lines = validated_response.split("\n")
    for i, line in enumerate(lines):
        if line.strip().startswith("Rewritten Response:"):
            return "\n".join(lines[i+1:]).strip()
    
    return response.strip()

def structure_response(response):
    structuring_prompt = f"Summarize the following response into a concise, short and well-structured format (don't use markdown format): {response}"
    structured_response = llm.invoke(structuring_prompt).content  
    return structured_response.strip()

def generate_response(instruction):
    try:
        refined_instruction = refine_instruction(instruction)
        search_result = agent.run(refined_instruction)
        validated_response = validate_response(search_result, instruction)
        final_response = structure_response(validated_response)
        return final_response
    except Exception as e:
        print(f"Error Generating Response: {e}")
        return "An error occurred while processing your request."
