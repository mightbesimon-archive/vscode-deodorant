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

from cgitb import text
from email import message
from pygls.lsp.methods import (
    HOVER,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    WORKSPACE_DID_CHANGE_CONFIGURATION,
)
from pygls.lsp.types import (
    ConfigurationItem,
    ConfigurationParams,
    DidChangeConfigurationParams,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    Hover,
    HoverParams,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
)
from pygls.server import LanguageServer

from qchecker.substructures import (
    SUBSTRUCTURES,
    Substructure,
)
from qchecker.match import TextRange


class PyDeodoriserServer(LanguageServer):
    CMD_SHOW_CONFIGURATION_ASYNC = 'showConfigurationAsync'
    CMD_SHOW_CONFIGURATION_CALLBACK = 'showConfigurationCallback'
    CMD_SHOW_CONFIGURATION_THREAD = 'showConfigurationThread'

    CONFIGURATION_SECTION = 'pyDeodoriser'
    WARNING_SOURCE = 'pyDeodoriser'

    def __init__(self):
        super().__init__()
        self.substructure_config = {}
        self.substructures = { sub.name: sub
            for sub in SUBSTRUCTURES
        } # dictionary of qcheckers substructures


pyDeodoriser = PyDeodoriserServer()


def _validate(ls: PyDeodoriserServer, params):
    text_doc = ls.workspace.get_document(params.text_document.uri)
    source = text_doc.source

    if not source: return   # guard clause
    # diagnostics = _validate_string(source) # for debugging

    diagnostics = [ diagnostic
        for name, sub in ls.substructures.items() if ls.substructure_config.get(name)
        for diagnostic in _validate_substructure(source, sub)
    ]

    ls.publish_diagnostics(text_doc.uri, diagnostics)



def _generate_diagnostic(text_range: TextRange, substructure: Substructure):
    diagnostic_range = Range(
        start=Position(line=text_range.from_line-1, character=text_range.from_offset),
        end=Position(line=text_range.to_line-1, character=text_range.to_offset),
    )
    return Diagnostic(
        range=diagnostic_range,
        message=substructure.technical_description,
        # message=substructure.description.content,
        source=PyDeodoriserServer.WARNING_SOURCE,
        severity = DiagnosticSeverity.Warning,
        code=substructure.name,
    )


def _validate_substructure(source: str, substructure: Substructure):
    """Flags matches of the substructure as warnings"""
    try:
        matches = substructure.iter_matches(source)
        return [_generate_diagnostic(match.text_range, substructure) for match in matches]
    except SyntaxError:
        return [] # do not return any diagnostics if code fails to parse


def _make_diagnostic(line, character, string):
    diagnostic_range = Range(
        start=Position(line=line, character=character),
        end=Position(line=line, character=character+len(string)),
    )
    return Diagnostic(
        range=diagnostic_range,
        message=f'Detected string "{string}"',
        source=PyDeodoriserServer.WARNING_SOURCE,
        severity = DiagnosticSeverity.Warning,
    )


def _validate_string(source, detect_string='hello world'):
    """Detects the specified string, default='hello world'."""

    return [ _make_diagnostic(idx, line.find(detect_string), detect_string)
        for idx, line in enumerate(source.split('\n')) if detect_string in line
    ]


def _contains(text_range: TextRange, position: Position):
    return text_range.from_line <= position.line <= text_range.to_line


def _check_hover(ls: PyDeodoriserServer, params: HoverParams):
    text_doc = ls.workspace.get_document(params.text_document.uri)
    source = text_doc.source

    match_ranges = [ (match.text_range, sub)
        for name, sub in ls.substructures.items() if ls.substructure_config.get(name)
        for match in sub.iter_matches(source)
    ]
    hover_match = [ (text_range, sub)
        for text_range, sub in match_ranges if _contains(text_range, params.position)
    ]

    if not hover_match: return

    text_range, substructure = hover_match[0]
    content = MarkupContent(
        kind=MarkupKind.Markdown,
        value=substructure.description.content,
    )
    hover_range = Range(
        start=Position(line=text_range.from_line-1, character=text_range.from_offset),
        end=Position(line=text_range.to_line-1, character=text_range.to_offset),
    )
    return Hover(contents=content, range=hover_range)


async def _get_substructure_config(ls: PyDeodoriserServer):
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
        ls.substructure_config = config[0].get('substructures')
        # ls.show_message(f'pyDeodoriser.substructures: {ls.substructure_config}')
    except Exception as e:
        ls.show_message_log(f'Config error: {e}')
        ls.show_message(f'Config error: {e}')

@pyDeodoriser.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: PyDeodoriserServer, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    _validate(ls, params)


@pyDeodoriser.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(ls: PyDeodoriserServer, params: DidCloseTextDocumentParams):
    """Text document did close notification."""
    # server.show_message('Text Document Did Close')


@pyDeodoriser.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: PyDeodoriserServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    # ls.show_message('Text Document Did Open')
    await _get_substructure_config(ls)
    _validate(ls, params)


# NOTE: currently not being registered for unknown reasons
@pyDeodoriser.feature(WORKSPACE_DID_CHANGE_CONFIGURATION)
async def did_change_configuration(ls: PyDeodoriserServer, params: DidChangeConfigurationParams):
    ls.show_message('Configuration Did Change')
    await _get_substructure_config(ls)


@pyDeodoriser.feature(HOVER)
def did_hover(ls: PyDeodoriserServer, params: HoverParams):
    return _check_hover(ls, params)
