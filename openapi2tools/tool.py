import json
import sys


def indentCode(indent, lines):
    # only indent from the 2nd line
    indented = [lines[0],  *
                (list(map(lambda line: ' ' * indent + line, lines[1:])))]
    return '\n'.join(indented)


def genType(dtype):
    match dtype:
        case 'integer':
            return 'int'
        case 'string':
            return 'str'
        case 'array':
            return 'list'
        case 'boolean':
            return 'bool'
        case 'number':
            return 'float'
        case _:
            raise RuntimeError(f'unexpected data type {dtype}')


def genToolCapabilities(indent, paths):
    def genCapability(pathBody):
        methods = pathBody.keys()
        return list(map(lambda method: f"+ use the `{pathBody[method]['operationId']}` tool to {pathBody[method]['summary'].lower()}", methods))

    capabilities = list(map(lambda key: genCapability(
        paths[key]), paths.keys()))
    capabilities = sum(capabilities, [])
    return indentCode(indent, capabilities)


def genTools(indent, clzName, paths, components):
    def genToolParameters(methodBody, components):
        def codegen(name, dtype, required=True):
            if required:
                return f'{name}: {genType(dtype)}'
            return f'{name}: Optional[{genType(dtype)}]'

        if 'parameters' in methodBody:
            paramList = list(map(lambda parameter: codegen(
                parameter['name'], parameter['schema']['type'], parameter['required']), methodBody['parameters']))
            return f"{', '.join(paramList)}"

        if 'requestBody' in methodBody:
            schema = methodBody['requestBody']['content']['application/json']['schema']['$ref']
            schema = schema[schema.rfind('/') + 1:]
            schemaDef = components['schemas'][schema]
            properties = list(filter(
                lambda property: property in schemaDef['required'], schemaDef['properties'].keys()))
            paramList = list(map(lambda property: codegen(
                property, schemaDef['properties'][property]['type']), properties))
            return f"{', '.join(paramList)}"

        return ''

    def genToolReturn(methodBody):
        schema = methodBody['responses']['200']['content']['application/json']['schema']
        if 'type' in schema:
            return genType(schema['type'])
        if '$ref' in schema:
            return 'dict'
        raise RuntimeError(f'unexpected tool return data type {schema}')

    def genHttpPath(path, methodBody):
        if 'parameters' in methodBody:
            parameters = list(
                filter(lambda parameter: parameter['in'] == 'query', methodBody['parameters']))
            queries = list(map(lambda parameter:
                               "f'" + parameter['name'] + '={' + parameter['name'] + '}' + '\' if ' + parameter['name'] + " != None else ''", parameters))
            queries = list(filter(lambda query: query != '', queries))
            queries = list(map(lambda query: f'({query})', queries))
            if len(queries) > 0:
                return f"f'{path}?' + " + " + '&' + ".join(queries)
        return f"f'{path}'"

    def genHttpBody(indent, methodBody, components):
        if 'requestBody' in methodBody and methodBody['requestBody']['required']:
            schema = methodBody['requestBody']['content']['application/json']['schema']['$ref']
            schema = schema[schema.rfind('/') + 1:]
            schemaDef = components['schemas'][schema]
            properties = list(filter(
                lambda property: property in schemaDef['required'], schemaDef['properties'].keys()))
            paramList = list(
                map(lambda property: f"{' ' * 4}'{property}': {property}, ", properties))
            lines = ['', 'data = {', *paramList, '}']
            return indentCode(indent, lines)
        return ''

    def genResponse(indent, methodBody):
        statuses = methodBody['responses'].keys()
        lines = []
        for index, status in enumerate(statuses):
            if index == 0:
                lines.append(f'if response.status_code == {status}:')
            else:
                lines.append(f'elif response.status_code == {status}:')
            lines.append(f"    return '{methodBody['responses'][status]['description']}' + '\\n\\n' + json.dumps(response.json(), indent = 2)")
        lines.append(f"return f'Request failed with status code: {{response.status_code}}'")
        return indentCode(indent, lines)

    def genTool(clzName, path, method, methodBody, components):
        print(f'    generating tool for {path} {method}')

        tool = f"""
@tool
def {methodBody['operationId']}({genToolParameters(methodBody, components)}) -> {genToolReturn(methodBody)}:
    '''{methodBody['summary']}'''
    {genHttpBody(4, methodBody, components)}
    response = requests.{method}({clzName}.BaseUrl + {genHttpPath(path, methodBody)}, headers={clzName}.HttpHeader{', json=data' if 'requestBody' in methodBody and methodBody['requestBody']['required'] else ''})
    {genResponse(4, methodBody)}
        """
        lines = tool.split('\n')[1:]
        return '\n'.join(lines)

    def genPath(clzName, pathName, pathBody, components):
        print(f'generating {pathName}')

        methods = pathBody.keys()
        tools = list(map(lambda method: genTool(
            clzName, pathName, method, pathBody[method], components), methods))
        return tools

    tools = list(map(lambda key: genPath(
        clzName, key, paths[key], components), paths.keys()))
    tools = sum(tools, [])
    tools = list(map(lambda tool: tool.split('\n'), tools))
    tools = sum(tools, [])
    return indentCode(indent, tools)


def genToolNames(indent, paths):
    def genPath(pathBody):
        methods = pathBody.keys()
        tools = list(
            map(lambda method: f"{pathBody[method]['operationId']},", methods))
        return tools

    tools = list(map(lambda key: genPath(
        paths[key]), paths.keys()))
    tools = sum(tools, [])
    return indentCode(indent, tools)


def convert(apiSpec, targetPy):
    spec = None
    with open(apiSpec, 'r') as file:
        spec = json.load(file)

    paths = spec['paths']
    components = spec['components']
    clzName = spec['info']['title'] + 'Api'

    clzBody = f"""
from typing import Optional
import requests
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig


class {clzName}:

    BaseUrl = 'YOUR_API_END_POINT'

    HttpHeader = {{
            'Content-Type': 'application/json',
            'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
        }}

    prompt = ChatPromptTemplate.from_messages(
    [
        (
            'system',
            '''You are a specialized {spec['info']['description']}. You can,

            {genToolCapabilities(12, paths)}
            
            Now answer your question'''
        ),
        ("placeholder", "{{messages}}"),
    ])

    {genTools(4, clzName, paths, components)}

    tools = [
        {genToolNames(8, paths)}
    ]

    def __init__(self, llm):
        self.runnable = {clzName}.prompt | llm.bind_tools({clzName}.tools)

    def __call__(self, state, config: RunnableConfig):
        configuration = config.get("configurable")
        {clzName}.BaseUrl = configuration.get('url', None)
        {clzName}.HttpHeader['Authorization'] = configuration.get('token', None)
        result = self.runnable.invoke(state)
        return {{'messages': result}}
    """

    lines = clzBody.split('\n')[1:]
    with open(targetPy, 'w') as wf:
        wf.write('\n'.join(lines))


def main():
    # tool description and usage
    print('\nopenapi2tools: Transform an OpenAPI specification into LangGraph tools\n')
    arguments = sys.argv
    if len(arguments) != 3:
        print('Usage: openapi2tools <your_openapi_spec.json> <target_file.py>')
        exit
    convert(arguments[1], arguments[2])

if __name__ == '__main__':
    main()