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
import asyncio
import json
import re
import time
import uuid
from json import JSONDecodeError
from typing import Optional

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

import ast

#from qchecker import IfElseReturnBool


class PyDeoderiserServer(LanguageServer):
    CMD_SHOW_CONFIGURATION_ASYNC = 'showConfigurationAsync'
    CMD_SHOW_CONFIGURATION_CALLBACK = 'showConfigurationCallback'
    CMD_SHOW_CONFIGURATION_THREAD = 'showConfigurationThread'

    CONFIGURATION_SECTION = 'pyDeoderiser'
    WARNING_SOURCE = 'pyDeoderiser'

    def __init__(self):
        super().__init__()


pyDeoderiser = PyDeoderiserServer()


def _validate(ls, params):
    ls.show_message_log('Validating json...')

    text_doc = ls.workspace.get_document(params.text_document.uri)

    source = text_doc.source
    #diagnostics = _validate_json(source) if source else []
    diagnostics = _validate_helloworld(source, ls) if source else []

    ls.publish_diagnostics(text_doc.uri, diagnostics)


def _generate_diagnostic(match, message):
    return Diagnostic(
                range=Range(
                    start=Position(line=match.from_line-1, character=match.from_offset-1),
                    end=Position(line=match.to_line-1, character=match.to_offset-1)
                ),
                message=message,
                source=PyDeoderiserServer.WARNING_SOURCE,
                severity = DiagnosticSeverity.Warning
            )


# def _validate_ifelsereturnbool(source, ls):
#     """Flags matches of the IfElseReturnBool pattern as warnings"""
#     try:
#         tree = ast.parse(source)
#         matches = IfElseReturnBool.iter_matches(tree)
#         ls.show_message_log(matches)

#         diagnostics = [_generate_diagnostic(match, "Placeholder message") for match in matches]

#         return diagnostics
#     except:
#         return [] # do not return any diagnostics if code fails to parse to AST


def _validate_helloworld(source, ls):
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
                source=PyDeoderiserServer.WARNING_SOURCE,
                severity = DiagnosticSeverity.Warning
            )

            diagnostics.append(d)
            start = index + 1
            index = line.find(detect_string, start)

        lineNum += 1

    return diagnostics


@pyDeoderiser.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _validate(ls, params)


@pyDeoderiser.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: PyDeoderiserServer, params: DidCloseTextDocumentParams):
    """Text document did close notification."""
    server.show_message('Text Document Did Close')


@pyDeoderiser.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    ls.show_message('Text Document Did Open')
    _validate(ls, params)


@pyDeoderiser.command(PyDeoderiserServer.CMD_SHOW_CONFIGURATION_ASYNC)
async def show_configuration_async(ls: PyDeoderiserServer, *args):
    """Gets exampleConfiguration from the client settings using coroutines."""
    try:
        config = await ls.get_configuration_async(
            ConfigurationParams(items=[
                ConfigurationItem(
                    scope_uri='',
                    section=PyDeoderiserServer.CONFIGURATION_SECTION)
        ]))

        example_config = config[0].get('exampleConfiguration')

        ls.show_message(f'pyDeoderiser.exampleConfiguration value: {example_config}')

    except Exception as e:
        ls.show_message_log(f'Error ocurred: {e}')


@pyDeoderiser.command(PyDeoderiserServer.CMD_SHOW_CONFIGURATION_CALLBACK)
def show_configuration_callback(ls: PyDeoderiserServer, *args):
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
            section=PyDeoderiserServer.CONFIGURATION_SECTION)
    ]), _config_callback)


@pyDeoderiser.thread()
@pyDeoderiser.command(PyDeoderiserServer.CMD_SHOW_CONFIGURATION_THREAD)
def show_configuration_thread(ls: PyDeoderiserServer, *args):
    """Gets exampleConfiguration from the client settings using thread pool."""
    try:
        config = ls.get_configuration(ConfigurationParams(items=[
            ConfigurationItem(
                scope_uri='',
                section=PyDeoderiserServer.CONFIGURATION_SECTION)
        ])).result(2)

        example_config = config[0].get('exampleConfiguration')

        ls.show_message(f'pyDeoderiser.exampleConfiguration value: {example_config}')

    except Exception as e:
        ls.show_message_log(f'Error ocurred: {e}')

