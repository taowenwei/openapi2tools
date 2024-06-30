# A chatbot implementation with an agent generated

The `movies.py` script implements a simple chatbot using the LangGraph graph builder, based on an [example](https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support/) from LangGraph documentation. 

While OpenAI's LLM is the default choice, it can be replaced with other LLMs, such as Ollama Llama3.

The `moviesAPi.py` is a code-generated script. Reference its [OpenAPI spec](../MockServer/openapi.json) at the `MockServer` folder

## Run the chatbot

1. Make sure you have an OpenAI API key
2. Run the app
3. Enter `.exit` to exit the conversation

A list of sample questions have been provided at the end of the `movies.py` file.

You can also enable LandSmith tracing as described [here](https://docs.smith.langchain.com/old/evaluation)