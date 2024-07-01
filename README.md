# <img src="./icon.png"/>openapi2tools

[![Release Notes](https://img.shields.io/github/release/langchain-ai/langchain?style=flat-square)](https://github.com/langchain-ai/langchain/releases)
[![PyPI - License](https://img.shields.io/pypi/l/langchain-core?style=flat-square)](https://opensource.org/licenses/MIT)

Convert an OpenAPI spec to LangGraph tools 🪄

## Concepts
1. [LangChain](https://python.langchain.com/v0.2/docs/introduction/) is a framework for developing apps powered by large language models (LLMs).
2. [LangGraph](https://langchain-ai.github.io/langgraph/), introduced by 
`LangChain` starting from v0.2, facilitates building [Agent](https://python.langchain.com/v0.2/docs/tutorials/agents/)-based apps that leverage and extend a LLM to perform tasks outside of its traditional domain. The heart of an agent is [Tool calls](https://python.langchain.com/v0.2/docs/how_to/tool_calling/#tool-calls).
3. [OpenAPI ](https://learn.openapis.org/introduction.html) Specification (OAS) is a standard format for defining APIs, allowing both humans and machines to understand the capabilities of a service without accessing its source code, documentation, or network traffic.

Companies worldwide have invested billions 💰💰💰 into developing APIs. In the new AI era, a question begs, how to leverage the power of natural language processing to consume the APIs while minimizing costs and maximizing existing investments.

**openapi2tools** addresses the challenge by converting and encapsulating an OpenAPI specification JSON into a domain-specific LangGraph `agent`, with each API represented as a `tool`.


## Installation and Usage

**openapi2tools** can be installed with pip,

```bash
pip install openapi2tools
```
After installation, you run the tool in a command line to generate an agent source file from a OpenAPI JSON ([example json](./MockServer/openapi.json))
```bash
openapi2tools <your_openapi_json_file> <output_python_file_name>
```

## Anatomy of an Agent for a Chatbot

The [MockServer folder](./MockServer/README.md) implements a REST API based service and provides an OpenAPI JSON ([openapi.json](./MockServer/openapi.json)). **openapi2tools** is supposed to run against the `openapi.json` to generate a fully encapsulated Agent ([moviesApi.py](./Chatbot/moviesApi.py)).

The [Chatbot folder](./Chatbot/README.md) contains an example implementation of a Chatbot ([movies.py](./Chatbot/movies.py)). It then utilizes the `Agent` generated above to call (a.k.a. `Tool calls`) the `Mockserver`, when a user chats with an OpenAI model.

### Anatomy of the `moviesApi` Agent

+ an engineered ChatPrompt
```python
prompt = ChatPromptTemplate.from_messages([
    ('system', 
        '''
        generate an overview from the `info.description`

        forEach api in openapi.json:
            generate a tool capability from `api.operationId` and `api.summary`
        '''
        ),
    ('placeholder', "{messages}")
])
```
+ a list of tools
```python
# for each api in openapi.json, 
# generate a tool in the following format,
    
'''
@tool
def `api.operationId` (`api.parameter list`) -> `api.response(HTTP 200)':
    `api.summary` as tool description

    response = requests call with `api.method` (`api.path`, `api.query`, `api.requestBody`)
    error handling from the listOf(`api.responses`)

...
tools = [
    the api.operationId list
]
'''
```
+ a class constructor to bind the prompt with a llm
```python
def __init__(self, llm):
    self.runnable = MoviesApi.prompt | llm.bind_tools(MoviesApi.tools)

```
+ an invoker to process a tool call
```python
def __call__(self, state, config: RunnableConfig):
    ...
    result = self.runnable.invoke(state)
    return {'messages': result}
```

## Known Issues
+ Supporting more authentication methods - currently only bearer token is implemented [here](https://github.com/taowenwei/openapi2tools/blob/86c8b58deeb645717e61c631db00c5210f5d5e67/Chatbot/moviesApi.py#L15).
+ Not sure how to support a HTTP body with arrays or embedded objects - currently expect a *flat* body schema.

## Contribution
This is an ongoing project, your contributions are extremely appreciated. Please create a Pull Request. 🍻🍻