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
    TextDocumentIdentifier,
)
from pygls.server import LanguageServer

from qchecker.substructures import (
    SUBSTRUCTURES,
    Substructure,
)
from qchecker.match import TextRange


class PyDeodoriserServer(LanguageServer):

    CMD_SHOW_CONFIGURATION_ASYNC = 'showConfigurationAsync'
    CONFIGURATION_SECTION = 'pyDeodoriser'
    DIAGNOSTIC_SOURCE = 'pyDeodoriser'

    def __init__(self):
        super().__init__()
        self.substructure_config = {}
        self.substructures = { sub.name: sub for sub in SUBSTRUCTURES }
        self.document = None
        self.matches = None

    async def get_config_substructure(self):
        try:
            config = await self.get_configuration_async(
                ConfigurationParams(items=[ ConfigurationItem(
                    scope_uri='', section=PyDeodoriserServer.CONFIGURATION_SECTION
                )])
            )
            self.substructure_config = config[0].get('substructures')
            self.show_message_log(f'pyDeodoriser.substructures: {self.substructure_config}')

        except Exception as e:
            self.show_message_log(f'Config error: {e}')


    def validate(self, document: TextDocumentIdentifier):
        self.document = self.workspace.get_document(document.uri)
        if not self.document.source: return

        print(f'[0]matches={self.matches}')
        self.matches = [ (match, sub)
            for name, sub in self.substructures.items() if self.substructure_config.get(name)
            for match in self._try_iter(sub, self.document.source)
        ]
        diagnostics = [
            self._make_diagnostic(match.text_range, substrcture)
            for match, substrcture in self.matches
        ]
        self.publish_diagnostics(self.document.uri, diagnostics)


    def hover(self, position: Position):
        hover_match = [ (match.text_range, substructure)
            for match, substructure in self.matches if self._contains(match.text_range, position)
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

    @staticmethod
    def _make_diagnostic(text_range: TextRange, substructure: Substructure):
        diagnostic_range = Range(
            start=Position(line=text_range.from_line-1, character=text_range.from_offset),
            end=Position(line=text_range.to_line-1, character=text_range.to_offset),
        )
        return Diagnostic(
            range=diagnostic_range,
            message=substructure.technical_description,
            source=PyDeodoriserServer.DIAGNOSTIC_SOURCE,
            severity = DiagnosticSeverity.Information,
            code=substructure.name,
        )

    @staticmethod
    def _try_iter(substructure: Substructure, source: str):
        try:
            return substructure.iter_matches(source)
        except:
            return []

    @staticmethod
    def _contains(text_range: TextRange, position: Position):
        return text_range.from_line <= position.line <= text_range.to_line



pyDeodoriser = PyDeodoriserServer()


@pyDeodoriser.feature(TEXT_DOCUMENT_DID_CHANGE)
async def did_change(ls: PyDeodoriserServer, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    await ls.get_config_substructure()
    ls.validate(params.text_document)


@pyDeodoriser.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: PyDeodoriserServer, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    await ls.get_config_substructure()
    ls.validate(params.text_document)


@pyDeodoriser.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(ls: PyDeodoriserServer, params: DidCloseTextDocumentParams):
    ls.refresh(params.text_document)


# NOTE: currently not being registered for unknown reasons
@pyDeodoriser.feature(WORKSPACE_DID_CHANGE_CONFIGURATION)
async def did_change_configuration(ls: PyDeodoriserServer, params: DidChangeConfigurationParams):
    ls.show_message('Configuration Did Change')
    await ls.get_config_substructure()


@pyDeodoriser.feature(HOVER)
def did_hover(ls: PyDeodoriserServer, params: HoverParams):
    return ls.hover(params.position)
