messages = {
    "check_uei_exists": "You did not provide a UEI on the coversheet",
    "check_uei_schema": "The auditee UEI is not valid",
    "check_uei_match": "The auditee UEI on the coversheet does not match the UEI entered in the General Information section",
    "check_cluster_names_state_cluster_missing": "You need to provide a state cluster name when selecting STATE CLUSTER",
    "check_cluster_names_no_state_cluster_needed": "State cluster must be blank unless you are selecting STATE CLUSTER",
    "check_other_cluster_names_cluster_name_missing": "You need to provide an altername cluster name when selecting OTHER CLUSTER",
    "check_other_cluster_names_no_other_cluster_needed": "Other cluster must be blank unless you are selecting OTHER CLUSTER",
    "check_direct_award_is_not_blank": "Direct award cannot be blank; it must be <b>Y</b> or <b>N</b>",
    "check_passthrough_name_when_no_direct": "If direct award is <b>N</b>, then you must provide a passthrough name",
    "check_passthrough_name_when_invalid_direct": "If direct award is <b>GSA_MIGRATION</b>, then passthrough name must not be blank",
    "check_loan_guarantee_empty_when_n": "When loan guarantee is <b>N</b>, outstanding balance must be empty",
    "check_loan_guarantee_present_when_y": "When loan guarantee is <b>Y</b>, there must be a loan balance",
    "check_is_right_workbook": "This is not the {} workbook",
    "check_no_major_program_no_type_when_n": "When major program is <b>N</b>, leave audit report type blank",
    "check_no_major_program_no_type_when_y": "When major program is <b>Y</b>, audit report type must be chosen",
    "check_no_repeat_findings_when_n": "When repeat findings from prior years is <b>N</b>, prior references must be <b>N/A</b>",
    "check_no_repeat_findings_when_y": "When repeat findings from prior years is <b>Y</b>, include prior year references",
    "check_missing_award_numbers": "Missing an award number",
    "check_missing_reference_numbers": "Missing a reference number",
    "check_missing_compliance_requirement": "Missing the type of compliance requirement",
    "check_missing_modified_opinion": "Missing modified opinion input",
    "check_missing_other_matters": "Missing other matters input",
    "check_missing_material_weakness": "Missing material weakness input",
    "check_missing_significant_deficiency": "Missing significant deficiency input",
    "check_missing_other_findings": "Missing other findings input",
    "check_missing_questioned_costs": "Missing questioned costs input",
    "check_missing_repeat_prior_reference": "Missing repeat findings from prior year",
    "check_missing_prior_references": "Missing prior year audit finding reference numbers",
    "check_missing_is_valid": "Missing findings combination validity",
    "check_missing_federal_agency_prefix": "Missing federal agency prefix",
    "check_missing_program_name": "Missing program name",
    "check_missing_amount_expended": "Missing amount expended",
    "check_missing_federal_program_total": "Missing federal program total",
    "check_missing_cluster_total": "Missing cluster total",
    "check_all_unique_award_numbers": "Repeated award number",
    "check_sequential_award_numbers_regex": "Award references should be of the form {}",
    "check_sequential_award_numbers_off": "Award reference is {}, but should be {}",
    "check_num_findings_always_present": "Number of audit findings must zero or greater",
    "check_missing_cluster_name": "Cluster name cannot be blank; select a name or N/A",
    "check_passthrough_name_when_yes_direct": "When direct award is <b>Y</b>, no passthrough name required",
    "check_no_major_program_is_blank": "Major program must be Y or N; cannot be left empty",
    "check_missing_loan_guaranteed": "Loan guarantee must be Y or N; cannot be left empty",
    "check_federal_award_passed_always_present": "Federal award passed must be Y or N; cannot be left empty",
    "check_passthrough_name_when_no_direct_n_and_empty_number": "When the award is direct, passthrough number must be empty",
    "check_findings_grid_validation": "The combination of findings <b>{}</b> is not a valid combination under Uniform Guidance",
    "check_eins_are_not_empty": "EIN cannot be empty",
    "check_ueis_are_not_empty": "UEI cannot be empty",
    "check_minimis_rate_used_is_not_blank": "An answer to <b>Did the auditee use the de minimis cost rate?</b> is required",
    "check_rate_explained_is_not_blank": "Explanation for rate usage is required",
    "check_accounting_policies_is_not_blank": "A description of the significant accounting policies is required",
    "check_note_title_is_not_blank": "Missing note title",
    "check_note_content_is_not_blank": "Missing note content",
    "check_contains_chart_or_table_is_not_blank": "An answer to <b>Did text contain a chart or table?</b> is required",
    "check_secondary_auditor_name_is_not_blank": "Missing audit firm/organization name",
    "check_secondary_auditor_ein_is_not_blank": "Missing audit firm/organization EIN",
    "check_secondary_auditor_address_street_is_not_blank": "Missing audit firm/organization address (number and street)",
    "check_secondary_auditor_address_city_is_not_blank": "Missing audit firm/organization city",
    "check_secondary_auditor_address_state_is_not_blank": "Missing audit firm/organization state",
    "check_secondary_auditor_address_zipcode_is_not_blank": "Missing audit firm/organization zip",
    "check_secondary_auditor_contact_name_is_not_blank": "Missing contact name",
    "check_secondary_auditor_contact_title_is_not_blank": "Missing contact title",
    "check_secondary_auditor_contact_phone_is_not_blank": "Missing contact phone number",
    "check_secondary_auditor_contact_email_is_not_blank": "Missing contact E-mail",
    "check_missing_text_of_finding": "Missing text of finding",
    "check_missing_planned_action": "Missing planned action",
    "check_invalid_y_or_n_entry": "<b>{}</b> is not accepted; please enter either <b>Y</b> or <b>N</b>",
    "check_missing_aln_three_digit_extension": "Missing ALN (CFDA) three digit extension",
    "check_aln_three_digit_extension_invalid": "The three digit extension should follow one of these formats: ###, RD#, or U##, where # represents a number",
    "check_prior_references_invalid": "Prior references must be <b>N/A</b> or a comma-separated list of values in the format <b>20##-###</b>, for example, <b>2019-001, 2019-002</b>",
    "check_finding_reference_invalid": "Finding references must be in the format <b>20##-###</b> where the first four digits are a year after 2010, for example, <b>2019-001, 2019-002</b>",
    "check_invalid_finding_reference_year": "The reference year in the finding reference <b>{}</b> declared in row {} does not match the audit year <b>{}</b>",
    "check_award_references_invalid": "Combining award references of 4 and 5-digit lengths is not allowed. If needed, zero-pad this number to make it 5 digits",
    "check_aln_prefix_invalid": "The federal agency prefix should be a two-digit value, for example, <b>10</b>",
    "check_additional_award_identification_present": "Missing additional award identification",
    "check_federal_program_total": "Federal program total is {}, but should be {}",
    "check_cluster_total": "This cluster total is {}, but should be {}",
    "check_total_amount_expended": "Total amount expended is {}, but should be {}",
    "check_federal_award_amount_passed_through_required": "When Federal Award Passed Through is <b>Y</b>, Amount Passed Through cannot be empty",
    "check_federal_award_amount_passed_through_not_allowed": "When Federal Award Passed Through is <b>N</b>, Amount Passed Through must be empty",
    "check_loan_balance": "The loan balance is currently set to {}. It should either be a positive number, N/A, or left empty",
    "check_cardinality_of_passthrough_names_and_ids": "You used a <b>|</b> (bar character) to indicate multiple passthrough names and IDs; you must provide equal numbers of names and IDs. You provided <b>{}</b> name{} and <b>{}</b> ID{}",
    "check_workbook_version": "Single audit workbook template version {} is not supported. Please download the latest workbook and transfer your data to it",
    "check_integer_values": "<b>{}</b> is not a valid integer",
    "check_gsa_migration_keyword": "<b>GSA_MIGRATION</b> is not allowed",
    "check_cluster_names": "Invalid cluster name",
    "check_award_references_len_4_or_5": "Award references must all follow the pattern AWARD-#### or AWARD-#####; {} does not fit either",
    "check_max_rows": "The number of rows in the {} named range exceeds the maximum allowed for this version of the workbook",
    "check_finding_uniqueness": "On row {}, you reported {}, and on row {}, you reported {}. The FAC cannot accept one finding reference with different finding details",
}
