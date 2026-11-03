from api_objects.faro.library.input.library_input import LibraryInput as ApiInformationReaderInput
from api_objects.faro.library.output.library_output import (LibraryOutput as ApiInformationReaderOutput, CompanyInfo, ScopeInfo, CompanyDocument, Agreement)
from library.information_reader import InformationReader
from library.information_reader_input import InformationReaderInput as LibInformationReaderInput


class InformationReaderEndpoint:
    def __init__(self, information_reader: InformationReader):
        self.information_reader = information_reader

    def handle(self, api_input: ApiInformationReaderInput) -> ApiInformationReaderOutput:
        information_reader_input = LibInformationReaderInput(company_id=api_input.company_id,
                                            permitted_scope_ids=api_input.permitted_scope_ids)
        result = self.information_reader.read(information_reader_input)
        return ApiInformationReaderOutput(supported_tasks=result.supported_tasks, groups=result.groups, reference_date=result.reference_date, company=CompanyInfo(company_id=result.company.company_id,
                                     name=result.company.name,
                                     timezone=result.company.timezone,
                                     data_version=result.company.data_version,
                                     definition_version=result.company.definition_version),
                                  scopes=[ScopeInfo(company_id=scope.company_id,
                                     scope_id=scope.scope_id,
                                     name=scope.name,
                                     aliases=scope.aliases) for scope in result.scopes],
                                  documents=[CompanyDocument(document_id=document.document_id,
                                     company_id=document.company_id,
                                     scope_ids=document.scope_ids,
                                     title=document.title,
                                     text=document.text,
                                     status=document.status,
                                     version=document.version,
                                     source=document.source,
                                     valid_from=document.valid_from) for document in result.documents],
                                  agreements=[Agreement(agreement_id=agreement.agreement_id,
                                     company_id=agreement.company_id,
                                     scope_id=agreement.scope_id,
                                     title=agreement.title,
                                     status=agreement.status,
                                     valid_from=agreement.valid_from,
                                     valid_until_exclusive=agreement.valid_until_exclusive,
                                     definition_id=agreement.definition_id,
                                     target=agreement.target,
                                     target_unit=agreement.target_unit,
                                     comparison=agreement.comparison,
                                     period_rule=agreement.period_rule,
                                     coverage_rule=agreement.coverage_rule,
                                     zero_hours_rule=agreement.zero_hours_rule,
                                     tie_rule=agreement.tie_rule,
                                     owner_role=agreement.owner_role,
                                     version=agreement.version) for agreement in result.agreements])
