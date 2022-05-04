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

from pygls.lsp.methods import (TEXT_DOCUMENT_DID_CHANGE,
                               TEXT_DOCUMENT_DID_CLOSE, TEXT_DOCUMENT_DID_OPEN, 
                               WORKSPACE_DID_CHANGE_CONFIGURATION)
from pygls.lsp.types import (ConfigurationItem, ConfigurationParams, 
                             DidChangeConfigurationParams,
                             Diagnostic, DiagnosticSeverity,
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

import qchecker.substructures


class PyDeodoriserServer(LanguageServer):
    CMD_SHOW_CONFIGURATION_ASYNC = 'showConfigurationAsync'
    CMD_SHOW_CONFIGURATION_CALLBACK = 'showConfigurationCallback'
    CMD_SHOW_CONFIGURATION_THREAD = 'showConfigurationThread'

    CONFIGURATION_SECTION = 'pyDeodoriser'
    WARNING_SOURCE = 'pyDeodoriser'

    def __init__(self):
        self.substructure_config = dict()
        self.substructures = dict([(name, cls) for name, cls in qchecker.substructures.__dict__.items() if isinstance(cls, type)]) # dictionary of qcheckers substructures
        super().__init__()


pyDeodoriser = PyDeodoriserServer()


def _validate(ls, params):
    text_doc = ls.workspace.get_document(params.text_document.uri)

    source = text_doc.source
    
    diagnostics = []
    if source:
        for substructure_name in ls.substructures.keys():
            if ls.substructure_config.get(substructure_name, False):
                diagnostics += _validate_substructure(source, ls.substructures[substructure_name])

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


def _validate_substructure(source, substructure):
    """Flags matches of the substructure as warnings"""
    try:
        matches = substructure.iter_matches(source)
        diagnostics = [_generate_diagnostic(match.text_range, substructure.technical_description) for match in matches]
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


async def _get_substructure_config(ls):
    """Retrieves a dictionary of the substructure config"""
    try:
        config = await ls.get_configuration_async(
            ConfigurationParams(items=[
                ConfigurationItem(
                    scope_uri='',
                    section=PyDeodoriserServer.CONFIGURATION_SECTION
                )
            ])
        )
        ls.substructure_config = config[0].get("substructures")
    except Exception as e:
        ls.show_message_log(f'Config error: {e}')


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
    await _get_substructure_config(ls)
    _validate(ls, params)


@pyDeodoriser.feature(WORKSPACE_DID_CHANGE_CONFIGURATION)
async def did_change_configuration(ls, params: DidChangeConfigurationParams):
    ls.show_message('Configuration Did Change')
    _get_substructure_config(ls)

