############################################################################
# Copyright(c) Open Law Library. All rights reserved.                      #
# See ThirdPartyNotices.txt in the project root for additional notices.    #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License")           #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http: // www.apache.org/licenses/LICENSE-2.0                         #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################

from pygls.lsp.methods import (COMPLETION, TEXT_DOCUMENT_DID_CHANGE,
                               TEXT_DOCUMENT_DID_CLOSE, TEXT_DOCUMENT_DID_OPEN, 
                               TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL)
from pygls.lsp.types import (CompletionItem, CompletionList, CompletionOptions,
                             CompletionParams, ConfigurationItem,
                             ConfigurationParams, Diagnostic, DiagnosticSeverity,
                             DidChangeTextDocumentParams, 
                             DidCloseTextDocumentParams,
                             DidOpenTextDocumentParams, MessageType, Position,
                             Range, Registration, RegistrationParams,
                             SemanticTokens, SemanticTokensLegend, SemanticTokensParams,
                             Unregistration, UnregistrationParams)
from pygls.lsp.types.basic_structures import (WorkDoneProgressBegin,
                                              WorkDoneProgressEnd,
                                              WorkDoneProgressReport)
from pygls.server import LanguageServer

from qchecker.substructures import IfElseReturnBool


class PyDeodoriserServer(LanguageServer):
    CMD_SHOW_CONFIGURATION_ASYNC = 'showConfigurationAsync'
    CMD_SHOW_CONFIGURATION_CALLBACK = 'showConfigurationCallback'
    CMD_SHOW_CONFIGURATION_THREAD = 'showConfigurationThread'

    CONFIGURATION_SECTION = 'pyDeoderiser'
    WARNING_SOURCE = 'pyDeoderiser'

    def __init__(self):
        super().__init__()


pyDeodoriser = PyDeodoriserServer()


def _validate(ls, params):
    ls.show_message_log('Validating json...')

    text_doc = ls.workspace.get_document(params.text_document.uri)

    source = text_doc.source
    diagnostics = _validate_ifelsereturnbool(source) if source else []
    #diagnostics = _validate_helloworld(source) if source else []

    ls.publish_diagnostics(text_doc.uri, diagnostics)


def _generate_diagnostic(text_range, message):
    return Diagnostic(
                range=Range(
                    start=Position(line=text_range.from_line-1, character=text_range.from_offset-1),
                    end=Position(line=text_range.to_line-1, character=text_range.to_offset-1)
                ),
                message=message,
                source=PyDeodoriserServer.WARNING_SOURCE,
                severity = DiagnosticSeverity.Warning
            )


def _validate_ifelsereturnbool(source):
    """Flags matches of the IfElseReturnBool pattern as warnings"""
    try:
        matches = IfElseReturnBool.iter_matches(source)
        diagnostics = [_generate_diagnostic(match.text_range, IfElseReturnBool.technical_description) for match in matches]
    except SyntaxError:
        diagnositics = [] # do not return any diagnostics if code fails to parse

    return diagnostics


def _validate_helloworld(source):
    """Detects the string 'hello world'."""
    detect_string = "hello world"
    diagnostics = []

    lineNum = 0
    for line in source.split("\n"):
        start = 0
        index = line.find(detect_string, start)
        while index != -1:
            d = Diagnostic(
                range=Range(
                    start=Position(line=lineNum, character=index),
                    end=Position(line=lineNum, character=index + len(detect_string))
                ),
                message="Hello!",
                source=PyDeodoriserServer.WARNING_SOURCE,
                severity = DiagnosticSeverity.Warning
            )

            diagnostics.append(d)
            start = index + 1
            index = line.find(detect_string, start)

        lineNum += 1

    return diagnostics


@pyDeodoriser.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _validate(ls, params)


@pyDeodoriser.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: PyDeodoriserServer, params: DidCloseTextDocumentParams):
    """Text document did close notification."""
    server.show_message('Text Document Did Close')


@pyDeodoriser.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message('Text Document Did Open')
    _validate(ls, params)


@pyDeodoriser.command(PyDeodoriserServer.CMD_SHOW_CONFIGURATION_ASYNC)
async def show_configuration_async(ls: PyDeodoriserServer, *args):
    """Gets exampleConfiguration from the client settings using coroutines."""
    try:
        config = await ls.get_configuration_async(
            ConfigurationParams(items=[
                ConfigurationItem(
                    scope_uri='',
                    section=PyDeodoriserServer.CONFIGURATION_SECTION)
        ]))

        example_config = config[0].get('exampleConfiguration')

        ls.show_message(f'pyDeoderiser.exampleConfiguration value: {example_config}')

    except Exception as e:
        ls.show_message_log(f'Error ocurred: {e}')


@pyDeodoriser.command(PyDeodoriserServer.CMD_SHOW_CONFIGURATION_CALLBACK)
def show_configuration_callback(ls: PyDeodoriserServer, *args):
    """Gets exampleConfiguration from the client settings using callback."""
    def _config_callback(config):
        try:
            example_config = config[0].get('exampleConfiguration')

            ls.show_message(f'pyDeoderiser.exampleConfiguration value: {example_config}')

        except Exception as e:
            ls.show_message_log(f'Error ocurred: {e}')

    ls.get_configuration(ConfigurationParams(items=[
        ConfigurationItem(
            scope_uri='',
            section=PyDeodoriserServer.CONFIGURATION_SECTION)
    ]), _config_callback)


@pyDeodoriser.thread()
@pyDeodoriser.command(PyDeodoriserServer.CMD_SHOW_CONFIGURATION_THREAD)
def show_configuration_thread(ls: PyDeodoriserServer, *args):
    """Gets exampleConfiguration from the client settings using thread pool."""
    try:
        config = ls.get_configuration(ConfigurationParams(items=[
            ConfigurationItem(
                scope_uri='',
                section=PyDeodoriserServer.CONFIGURATION_SECTION)
        ])).result(2)

        example_config = config[0].get('exampleConfiguration')

        ls.show_message(f'pyDeoderiser.exampleConfiguration value: {example_config}')

    except Exception as e:
        ls.show_message_log(f'Error ocurred: {e}')

