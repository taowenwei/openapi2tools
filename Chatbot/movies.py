from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition, ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_openai import ChatOpenAI
from langgraph.graph.message import AnyMessage, add_messages
from typing import Annotated
from typing_extensions import TypedDict

# the agent, generated from an OpenAPI json file
import moviesApi


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


# build a LangGraph graph with an agent, tools and memory
llm = ChatOpenAI(model='gpt-3.5-turbo')
builder = StateGraph(State)
builder.add_node('movieAssistant', moviesApi.MoviesApi(llm))
builder.add_node('tools', ToolNode(moviesApi.MoviesApi.tools))
builder.add_conditional_edges(
    'movieAssistant',
    tools_condition,
)
builder.add_edge('tools', 'movieAssistant')
builder.set_entry_point('movieAssistant')
graph = builder.compile(checkpointer=SqliteSaver.from_conn_string(':memory:'))

# build a conversation thread
config = {'configurable': {'thread_id': '1',
                           # mock server URL and mock API token
                           'url': 'http://localhost:4000', 'token': '1234567890'}}
while True:
    user_input = input('You: ')
    if user_input == '.exit':
        print('bye bye')
        break

    events = graph.stream(
        {"messages": [("user", user_input)]}, config, stream_mode="values")
    for event in events:
        if "messages" in event:
            event["messages"][-1].pretty_print()

# Example questions:
# user_input = 'get all the movies released on 2008'
# user_input = 'retrieve all the movie release years'
# user_input = 'get the movie with id=2'
# user_input = 'create a new movie with title="Despicable Me 4", year=2024'
