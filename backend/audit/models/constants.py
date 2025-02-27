from django.utils.translation import gettext_lazy as _
from collections import namedtuple as nt


class STATUS:
    """
    The possible states of a submission.
    """

    IN_PROGRESS = "in_progress"
    READY_FOR_CERTIFICATION = "ready_for_certification"
    AUDITOR_CERTIFIED = "auditor_certified"
    AUDITEE_CERTIFIED = "auditee_certified"
    CERTIFIED = "certified"
    SUBMITTED = "submitted"
    DISSEMINATED = "disseminated"
    FLAGGED_FOR_REMOVAL = "flagged_for_removal"


STATUS_CHOICES = (
    (STATUS.IN_PROGRESS, "In Progress"),
    (STATUS.FLAGGED_FOR_REMOVAL, "Flagged for Removal"),
    (STATUS.READY_FOR_CERTIFICATION, "Ready for Certification"),
    (STATUS.AUDITOR_CERTIFIED, "Auditor Certified"),
    (STATUS.AUDITEE_CERTIFIED, "Auditee Certified"),
    (STATUS.CERTIFIED, "Certified"),
    (STATUS.SUBMITTED, "Submitted"),
    (STATUS.DISSEMINATED, "Disseminated"),
)


class AuditType:
    SINGLE_AUDIT = "single_audit"
    PROGRAM_SPECIFIC = "program_specific"


AUDIT_TYPE_CODES = (
    (AuditType.SINGLE_AUDIT, _("Single Audit")),
    (AuditType.PROGRAM_SPECIFIC, _("Program-Specific Audit")),
)


class SubmissionEventType:
    ACCESS_GRANTED = "access-granted"
    ADDITIONAL_EINS_UPDATED = "additional-eins-updated"
    ADDITIONAL_EINS_DELETED = "additional-eins-deleted"
    ADDITIONAL_UEIS_UPDATED = "additional-ueis-updated"
    ADDITIONAL_UEIS_DELETED = "additional-ueis-deleted"
    AUDIT_INFORMATION_UPDATED = "audit-information-updated"
    AUDIT_REPORT_PDF_UPDATED = "audit-report-pdf-updated"
    AUDITEE_CERTIFICATION_COMPLETED = "auditee-certification-completed"
    AUDITOR_CERTIFICATION_COMPLETED = "auditor-certification-completed"
    CORRECTIVE_ACTION_PLAN_UPDATED = "corrective-action-plan-updated"
    CORRECTIVE_ACTION_PLAN_DELETED = "corrective-action-plan-deleted"
    CREATED = "created"
    FEDERAL_AWARDS_UPDATED = "federal-awards-updated"
    FEDERAL_AWARDS_AUDIT_FINDINGS_UPDATED = "federal-awards-audit-findings-updated"
    FEDERAL_AWARDS_AUDIT_FINDINGS_DELETED = "federal-awards-audit-findings-deleted"
    FEDERAL_AWARDS_AUDIT_FINDINGS_TEXT_UPDATED = (
        "federal-awards-audit-findings-text-updated"
    )
    FEDERAL_AWARDS_AUDIT_FINDINGS_TEXT_DELETED = (
        "federal-awards-audit-findings-text-deleted"
    )
    FINDINGS_UNIFORM_GUIDANCE_UPDATED = "findings-uniform-guidance-updated"
    FINDINGS_UNIFORM_GUIDANCE_DELETED = "findings-uniform-guidance-deleted"
    GENERAL_INFORMATION_UPDATED = "general-information-updated"
    LOCKED_FOR_CERTIFICATION = "locked-for-certification"
    UNLOCKED_AFTER_CERTIFICATION = "unlocked-after-certification"
    NOTES_TO_SEFA_UPDATED = "notes-to-sefa-updated"
    SECONDARY_AUDITORS_UPDATED = "secondary-auditors-updated"
    SECONDARY_AUDITORS_DELETED = "secondary-auditors-deleted"
    SUBMITTED = "submitted"
    DISSEMINATED = "disseminated"
    TRIBAL_CONSENT_UPDATED = "tribal-consent-updated"
    FLAGGED_SUBMISSION_FOR_REMOVAL = "flagged-submission-for-removal"
    CANCEL_REMOVAL_FLAG = "cancel-removal-flag"


SUBMISSION_EVENT_TYPES = (
    (SubmissionEventType.ACCESS_GRANTED, _("Access granted")),
    (SubmissionEventType.ADDITIONAL_EINS_UPDATED, _("Additional EINs updated")),
    (SubmissionEventType.ADDITIONAL_EINS_DELETED, _("Additional EINs deleted")),
    (SubmissionEventType.ADDITIONAL_UEIS_UPDATED, _("Additional UEIs updated")),
    (SubmissionEventType.ADDITIONAL_UEIS_DELETED, _("Additional UEIs deleted")),
    (SubmissionEventType.AUDIT_INFORMATION_UPDATED, _("Audit information updated")),
    (SubmissionEventType.AUDIT_REPORT_PDF_UPDATED, _("Audit report PDF updated")),
    (
        SubmissionEventType.AUDITEE_CERTIFICATION_COMPLETED,
        _("Auditee certification completed"),
    ),
    (
        SubmissionEventType.AUDITOR_CERTIFICATION_COMPLETED,
        _("Auditor certification completed"),
    ),
    (
        SubmissionEventType.CORRECTIVE_ACTION_PLAN_UPDATED,
        _("Corrective action plan updated"),
    ),
    (
        SubmissionEventType.CORRECTIVE_ACTION_PLAN_DELETED,
        _("Corrective action plan deleted"),
    ),
    (SubmissionEventType.CREATED, _("Created")),
    (SubmissionEventType.FEDERAL_AWARDS_UPDATED, _("Federal awards updated")),
    (
        SubmissionEventType.FEDERAL_AWARDS_AUDIT_FINDINGS_UPDATED,
        _("Federal awards audit findings updated"),
    ),
    (
        SubmissionEventType.FEDERAL_AWARDS_AUDIT_FINDINGS_DELETED,
        _("Federal awards audit findings deleted"),
    ),
    (
        SubmissionEventType.FEDERAL_AWARDS_AUDIT_FINDINGS_TEXT_UPDATED,
        _("Federal awards audit findings text updated"),
    ),
    (
        SubmissionEventType.FEDERAL_AWARDS_AUDIT_FINDINGS_TEXT_DELETED,
        _("Federal awards audit findings text deleted"),
    ),
    (
        SubmissionEventType.FINDINGS_UNIFORM_GUIDANCE_UPDATED,
        _("Findings uniform guidance updated"),
    ),
    (
        SubmissionEventType.FINDINGS_UNIFORM_GUIDANCE_DELETED,
        _("Findings uniform guidance deleted"),
    ),
    (SubmissionEventType.GENERAL_INFORMATION_UPDATED, _("General information updated")),
    (SubmissionEventType.LOCKED_FOR_CERTIFICATION, _("Locked for certification")),
    (
        SubmissionEventType.UNLOCKED_AFTER_CERTIFICATION,
        _("Unlocked after certification"),
    ),
    (SubmissionEventType.NOTES_TO_SEFA_UPDATED, _("Notes to SEFA updated")),
    (SubmissionEventType.SECONDARY_AUDITORS_UPDATED, _("Secondary auditors updated")),
    (SubmissionEventType.SECONDARY_AUDITORS_DELETED, _("Secondary auditors deleted")),
    (SubmissionEventType.SUBMITTED, _("Submitted to the FAC for processing")),
    (SubmissionEventType.DISSEMINATED, _("Copied to dissemination tables")),
    (SubmissionEventType.TRIBAL_CONSENT_UPDATED, _("Tribal audit consent updated")),
    (
        SubmissionEventType.FLAGGED_SUBMISSION_FOR_REMOVAL,
        _("Flagged submission for removal"),
    ),
    (SubmissionEventType.CANCEL_REMOVAL_FLAG, _("Cancel removal flag")),
)


class FindingsBitmask:
    MODIFIED_OPINION = 1  # 0b0000001
    OTHER_FINDINGS = 2  # 0b0000010
    MATERIAL_WEAKNESS = 4  # 0b0000100
    SIGNIFICANT_DEFICIENCY = 8  # 0b0001000
    OTHER_MATTERS = 16  # 0b0010000
    QUESTIONED_COSTS = 32  # 0b0100000
    REPEAT_FINDING = 64  # 0b1000000
    ALL = 127  # 0b1111111


FindingsFieldBitmask = nt("FindingsFieldBitmask", ["field", "search_param", "mask"])
FINDINGS_FIELD_TO_BITMASK = [
    FindingsFieldBitmask(
        field="modified_opinion",
        search_param="is_modified_opinion",
        mask=FindingsBitmask.MODIFIED_OPINION,
    ),
    FindingsFieldBitmask(
        field="other_findings",
        search_param="is_other_findings",
        mask=FindingsBitmask.OTHER_FINDINGS,
    ),
    FindingsFieldBitmask(
        field="material_weakness",
        search_param="is_material_weakness",
        mask=FindingsBitmask.MATERIAL_WEAKNESS,
    ),
    FindingsFieldBitmask(
        field="significant_deficiency",
        search_param="is_significant_deficiency",
        mask=FindingsBitmask.SIGNIFICANT_DEFICIENCY,
    ),
    FindingsFieldBitmask(
        field="other_matters",
        search_param="is_other_matters",
        mask=FindingsBitmask.OTHER_MATTERS,
    ),
    FindingsFieldBitmask(
        field="questioned_costs",
        search_param="is_questioned_costs",
        mask=FindingsBitmask.QUESTIONED_COSTS,
    ),
    # This is a special case handled by dissemination, but works using this in search
    FindingsFieldBitmask(
        field="_blank_",
        search_param="is_repeat_finding",
        mask=FindingsBitmask.REPEAT_FINDING,
    ),
]
