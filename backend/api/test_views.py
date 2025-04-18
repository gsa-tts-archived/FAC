import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from rest_framework.test import APIClient

from api.test_uei import valid_uei_results
from audit.models import Access, Audit, SingleAuditChecklist

User = get_user_model()

ELIGIBILITY_PATH = reverse("api-eligibility")
AUDITEE_INFO_PATH = reverse("api-auditee-info")
ACCESS_AND_SUBMISSION_PATH = reverse("api-accessandsubmission")
SUBMISSIONS_PATH = reverse("submissions")
ACCESS_LIST_PATH = reverse("access-list")


VALID_AUDITEE_INFO_DATA = {
    "auditee_uei": "ZQGGHJH74DW7",
    "auditee_fiscal_period_start": "2021-01-01",
    "auditee_fiscal_period_end": "2022-01-01",
    "auditee_name": "Tester",
}

VALID_ELIGIBILITY_DATA = {
    "is_usa_based": True,
    "met_spending_threshold": True,
    "user_provided_organization_type": "state",
}

VALID_ACCESS_AND_SUBMISSION_DATA = {
    "certifying_auditee_contact_email": "a@a.com",
    "certifying_auditee_contact_fullname": "Full Name",
    "certifying_auditor_contact_email": "b@b.com",
    "certifying_auditor_contact_fullname": "Full Name",
    "auditee_contacts_email": ["c@c.com"],
    "auditee_contacts_fullname": ["Name"],
    "auditor_contacts_email": ["d@d.com"],
    "auditor_contacts_fullname": ["Name"],
}

EMAIL_TO_ROLE = {
    "certifying_auditee_contact_email": "certifying_auditee_contact",
    "certifying_auditor_contact_email": "certifying_auditor_contact",
    "auditee_contacts_email": "editor",
    "auditor_contacts_email": "editor",
}

SAMPLE_BASE_SAC_DATA = {
    # 0. Meta data
    "submitted_by": None,
    "date_created": "2022-08-11",
    "submission_status": "in_progress",
    "report_id": "2022ABC1000023",
    "audit_type": "single-audit",
    # Part 1: General Information
    "general_information": {
        "auditee_fiscal_period_start": "2021-10-01",
        "auditee_fiscal_period_end": "2022-10-01",
        "audit_period_covered": "annual",
        "ein": "123456789",
        "ein_not_an_ssn_attestation": True,
        "multiple_eins_covered": False,
        "auditee_uei": "ZQGGHJH74DW7",
        "multiple_ueis_covered": False,
        "auditee_name": "Auditee McAudited",
        "auditee_address_line_1": "200 feet into left field",
        "auditee_city": "New York",
        "auditee_state": "NY",
        "auditee_zip": "10451",
        "auditee_contact_name": "Designate Representative",
        "auditee_contact_title": "Lord of Doors",
        "auditee_phone": "5558675309",
        "auditee_email": "auditee.mcaudited@leftfield.com",
        "user_provided_organization_type": "local",
        "met_spending_threshold": True,
        "is_usa_based": True,
        "auditor_firm_name": "Dollar Audit Store",
        "auditor_ein": "987654321",
        "auditor_ein_not_an_ssn_attestation": True,
        "auditor_country": "USA",
        "auditor_address_line_1": "100 Percent Respectable St.",
        "auditor_city": "Podunk",
        "auditor_international_address": """
            55, Rue du Faubourg Saint-Honoré, 75008 Paris, France
        """,
        "auditor_state": "NY",
        "auditor_zip": "14886",
        "auditor_contact_name": "Qualified Human Accountant",
        "auditor_contact_title": "Just an ordinary person",
        "auditor_phone": "0008675309",
        "auditor_email": "qualified.human.accountant@dollarauditstore.com",
    },
}


def omit(remove, d) -> dict:
    """omit(["a"], {"a":1, "b": 2}) => {"b": 2}"""
    return {k: d[k] for k in d if k not in remove}


class EligibilityViewTests(TestCase):
    INELIGIBLE = {
        "is_usa_based": False,
        "met_spending_threshold": True,
        "user_provided_organization_type": "state",
    }

    def test_auth_required(self):
        """
        Unauthenticated requests return a 403 response
        DRF's IsAuthenticated permission class returns a 403 instead of a 401, see docs below
        https://www.django-rest-framework.org/api-guide/permissions/#how-permissions-are-determined
        """
        client = APIClient()
        response = client.post(ELIGIBILITY_PATH, VALID_ELIGIBILITY_DATA, format="json")
        self.assertEqual(response.status_code, 403)

    def test_success_and_failure(self):
        """
        An authenticated request receives an eligible response and an ineligible response
        """
        client = APIClient()
        user = baker.make(User)
        client.force_authenticate(user=user)

        response = client.post(ELIGIBILITY_PATH, VALID_ELIGIBILITY_DATA, format="json")
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["eligible"], True)

        response = client.post(ELIGIBILITY_PATH, self.INELIGIBLE, format="json")
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["eligible"], False)


class UEIValidationViewTests(TestCase):
    PATH = reverse("api-uei-validation")
    SUCCESS = {"auditee_uei": "ZQGGHJH74DW7"}
    INELIGIBLE = {"auditee_uei": "000000000OI*"}

    def test_auth_required(self):
        """
        Unauthenticated requests return unauthorized response
        DRF's IsAuthenticated permission class returns a 403 instead of a 401, see docs below
        https://www.django-rest-framework.org/api-guide/permissions/#how-permissions-are-determined
        """
        client = APIClient()
        response = client.post(self.PATH, self.SUCCESS, format="json")
        self.assertEqual(response.status_code, 403)

    def test_success_and_failure(self):
        """
        An authenticated request receives an eligible response and an ineligible response
        """
        client = APIClient()
        user = baker.make(User)
        client.force_authenticate(user=user)

        # Valid
        with patch("api.uei.SESSION.get") as mock_get:
            mock_get.return_value.status_code = 200  # Mock the status code
            mock_get.return_value.json.return_value = json.loads(
                valid_uei_results
            )  # Mock the json

            response = client.post(self.PATH, self.SUCCESS, format="json")
            data = response.json()
            valid_uei_results_json_entity = json.loads(valid_uei_results)["entityData"][
                0
            ]["entityRegistration"]
            valid_uei_results_json_coredata = json.loads(valid_uei_results)[
                "entityData"
            ][0]["coreData"]

            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["valid"], True)
            self.assertEqual(
                data["response"]["auditee_uei"], valid_uei_results_json_entity["ueiSAM"]
            )
            self.assertEqual(
                data["response"]["auditee_name"],
                valid_uei_results_json_entity["legalBusinessName"],
            )
            self.assertEqual(
                data["response"]["auditee_fiscal_year_end_date"],
                valid_uei_results_json_coredata["entityInformation"][
                    "fiscalYearEndCloseDate"
                ],
            )
            self.assertEqual(
                data["response"]["auditee_address_line_1"],
                valid_uei_results_json_coredata["mailingAddress"]["addressLine1"],
            )
            self.assertEqual(
                data["response"]["auditee_city"],
                valid_uei_results_json_coredata["mailingAddress"]["city"],
            )
            self.assertEqual(
                data["response"]["auditee_state"],
                valid_uei_results_json_coredata["mailingAddress"][
                    "stateOrProvinceCode"
                ],
            )
            self.assertEqual(
                data["response"]["auditee_zip"],
                valid_uei_results_json_coredata["mailingAddress"]["zipCode"],
            )

        response = client.post(self.PATH, self.INELIGIBLE, format="json")
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["valid"], False)


class AuditeeInfoTests(TestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_missing_expected_form_data_from_prior_step(self):
        """Return an error and point to Eligibility step if we're missing data from that step in the user's profile"""
        response = self.client.post(
            AUDITEE_INFO_PATH, VALID_AUDITEE_INFO_DATA, format="json"
        )
        data = response.json()
        self.assertEqual(data["next"], ELIGIBILITY_PATH)
        self.assertTrue(data["errors"])

    def test_valid_data_updates_profile(self):
        """Valid POST update user's form data stored in their profile"""
        # Add eligibility data to profile
        self.user.profile.entry_form_data = VALID_ELIGIBILITY_DATA
        self.user.profile.save()

        response = self.client.post(
            AUDITEE_INFO_PATH, VALID_AUDITEE_INFO_DATA, format="json"
        )
        data = response.json()
        self.assertEqual(data["next"], ACCESS_AND_SUBMISSION_PATH)
        self.assertEqual(
            self.user.profile.entry_form_data,
            VALID_ELIGIBILITY_DATA | VALID_AUDITEE_INFO_DATA,
        )

    # 2023-05-30: We're proceeding with the assumption that as a matter of
    # policy we can reject audits without UEIs. If that turns out to be untrue,
    # we'll uncomment these three tests.
    # def test_null_auditee_uei(self):
    #     """
    #     Auditee UEI can be null
    #     """
    #     self.user.profile.entry_form_data = VALID_ELIGIBILITY_DATA
    #     self.user.profile.save()
    #     input_data = VALID_AUDITEE_INFO_DATA | {"auditee_uei": None}
    #     response = self.client.post(AUDITEE_INFO_PATH, input_data, format="json")
    #     data = response.json()
    #     self.assertEqual(data["next"], ACCESS_AND_SUBMISSION_PATH)
    #     self.assertEqual(
    #         self.user.profile.entry_form_data, VALID_ELIGIBILITY_DATA | input_data
    #     )

    # def test_blank_auditee_uei(self):
    #     """
    #     Auditee UEI can be blank
    #     """
    #     self.user.profile.entry_form_data = VALID_ELIGIBILITY_DATA
    #     self.user.profile.save()
    #     input_data = VALID_AUDITEE_INFO_DATA | {"auditee_uei": ""}
    #     response = self.client.post(AUDITEE_INFO_PATH, input_data, format="json")
    #     data = response.json()
    #     self.assertEqual(data["next"], ACCESS_AND_SUBMISSION_PATH)
    #     self.assertEqual(
    #         self.user.profile.entry_form_data, VALID_ELIGIBILITY_DATA | input_data
    #     )

    # def test_missing_auditee_uei(self):
    #     """
    #     Auditee UEI can be missing
    #     """
    #     self.user.profile.entry_form_data = VALID_ELIGIBILITY_DATA
    #     self.user.profile.save()
    #     input_data = VALID_AUDITEE_INFO_DATA.copy()
    #     del input_data["auditee_uei"]
    #     response = self.client.post(AUDITEE_INFO_PATH, input_data, format="json")
    #     data = response.json()
    #     self.assertEqual(data["next"], ACCESS_AND_SUBMISSION_PATH)
    #     self.assertEqual(
    #         self.user.profile.entry_form_data, VALID_ELIGIBILITY_DATA | input_data
    #     )

    def test_blank_auditee_name(self):
        """
        Auditee name can be blank
        """
        self.user.profile.entry_form_data = VALID_ELIGIBILITY_DATA
        self.user.profile.save()
        input_data = VALID_AUDITEE_INFO_DATA | {"auditee_name": ""}
        response = self.client.post(AUDITEE_INFO_PATH, input_data, format="json")
        data = response.json()
        self.assertEqual(data["next"], ACCESS_AND_SUBMISSION_PATH)
        self.assertEqual(
            self.user.profile.entry_form_data, VALID_ELIGIBILITY_DATA | input_data
        )

    # FIXME MSHD: This test is wrong (None is not an option), the following
    # test is more accurate. Also, we are going to remove the API post endpoint.
    #
    # def test_null_auditee_name(self):
    #     """
    #     Auditee name can be null
    #     """
    #     self.user.profile.entry_form_data = VALID_ELIGIBILITY_DATA
    #     self.user.profile.save()
    #     input_data = VALID_AUDITEE_INFO_DATA | {"auditee_name": None}
    #     response = self.client.post(AUDITEE_INFO_PATH, input_data, format="json")
    #     data = response.json()
    #     self.assertEqual(data["next"], ACCESS_AND_SUBMISSION_PATH)
    #     self.assertEqual(
    #         self.user.profile.entry_form_data, VALID_ELIGIBILITY_DATA | input_data
    #     )

    def test_missing_auditee_name(self):
        """
        Auditee name can be missing
        """
        self.user.profile.entry_form_data = VALID_ELIGIBILITY_DATA
        self.user.profile.save()
        input_data = VALID_AUDITEE_INFO_DATA.copy()
        del input_data["auditee_name"]
        response = self.client.post(AUDITEE_INFO_PATH, input_data, format="json")
        data = response.json()
        self.assertEqual(data["next"], ACCESS_AND_SUBMISSION_PATH)
        self.assertEqual(
            self.user.profile.entry_form_data, VALID_ELIGIBILITY_DATA | input_data
        )

    def test_missing_auditee_fiscal_period_start(self):
        """
        Auditee fiscal period start cannot be missing
        """
        self.user.profile.entry_form_data = VALID_ELIGIBILITY_DATA
        self.user.profile.save()
        input_data = VALID_AUDITEE_INFO_DATA.copy()
        del input_data["auditee_fiscal_period_start"]
        response = self.client.post(AUDITEE_INFO_PATH, input_data, format="json")
        data = response.json()
        self.assertTrue(data["errors"])

    def test_missing_auditee_fiscal_period_end(self):
        """
        Auditee fiscal period end cannot be missing
        """
        self.user.profile.entry_form_data = VALID_ELIGIBILITY_DATA
        self.user.profile.save()
        input_data = VALID_AUDITEE_INFO_DATA.copy()
        del input_data["auditee_fiscal_period_end"]
        response = self.client.post(AUDITEE_INFO_PATH, input_data, format="json")
        data = response.json()
        self.assertTrue(data["errors"])


class AccessAndSubmissionTests(TestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_missing_expected_form_data_from_prior_steps(self):
        """Return an error and point to Eligibility step if we're missing data from any prior step"""
        # Missing Eligibility data
        response = self.client.post(
            ACCESS_AND_SUBMISSION_PATH, VALID_ACCESS_AND_SUBMISSION_DATA, format="json"
        )
        data = response.json()
        self.assertEqual(data["next"], ELIGIBILITY_PATH)
        self.assertTrue(data["errors"])

        self.user.profile.entry_form_data = VALID_ELIGIBILITY_DATA
        self.user.profile.save()

        # Have eligibility, but missing auditee info data
        response = self.client.post(
            ACCESS_AND_SUBMISSION_PATH, VALID_ACCESS_AND_SUBMISSION_DATA, format="json"
        )
        data = response.json()
        self.assertEqual(data["next"], ELIGIBILITY_PATH)
        self.assertTrue(data["errors"])

    def test_valid_data_creates_SAC_and_Access(self):
        """A new SAC is created along with related Access instances"""
        # Add eligibility and Auditee Info data to profile
        self.user.profile.entry_form_data = (
            VALID_ELIGIBILITY_DATA | VALID_AUDITEE_INFO_DATA
        )
        self.user.profile.save()

        # Create a user to check that association happens on Access creation:
        catcdotcom = baker.make(User, email="c@c.com")

        response = self.client.post(
            ACCESS_AND_SUBMISSION_PATH, VALID_ACCESS_AND_SUBMISSION_DATA, format="json"
        )
        data = response.json()

        audit = Audit.objects.get(report_id=data["report_id"])

        certifying_auditee_contact_access = Access.objects.get(
            audit=audit, role="certifying_auditee_contact"
        )
        certifying_auditor_contact_access = Access.objects.get(
            audit=audit, role="certifying_auditor_contact"
        )

        editors = Access.objects.filter(audit=audit, role="editor")
        editor_emails = [acc.email for acc in editors]
        editor_users = [acc.user for acc in editors]

        self.assertEqual(audit.created_by, self.user)
        self.assertTrue(self.user.email in editor_emails)
        self.assertTrue("c@c.com" in editor_emails)
        self.assertTrue("d@d.com" in editor_emails)
        self.assertEqual(certifying_auditee_contact_access.email, "a@a.com")
        self.assertEqual(certifying_auditor_contact_access.email, "b@b.com")

        # Check that existing user was associated without having had to log in:
        self.assertIn(catcdotcom, editor_users)

    def test_multiple_auditee_auditor_contacts(self):
        """A new SAC is created along with related Access instances"""
        # Add eligibility and Auditee Info data to profile
        self.user.profile.entry_form_data = (
            VALID_ELIGIBILITY_DATA | VALID_AUDITEE_INFO_DATA
        )
        self.user.profile.save()

        access_and_submission_data = VALID_ACCESS_AND_SUBMISSION_DATA.copy()
        access_and_submission_data["auditee_contacts_email"].append("e@e.com")
        access_and_submission_data["auditor_contacts_email"].append("f@f.com")
        access_and_submission_data["auditee_contacts_fullname"].append("Real Name")
        access_and_submission_data["auditor_contacts_fullname"].append("Real Name")

        response = self.client.post(
            ACCESS_AND_SUBMISSION_PATH, access_and_submission_data, format="json"
        )
        data = response.json()

        audit = Audit.objects.get(report_id=data["report_id"])

        editors = (
            Access.objects.filter(audit=audit, role="editor")
            .values_list("email", flat=True)
            .order_by("email")
        )

        submitted_contacts = (
            access_and_submission_data["auditee_contacts_email"]
            + access_and_submission_data["auditor_contacts_email"]
        )

        for db_addr, form_addr in zip(filter(None, editors), submitted_contacts):
            self.assertTrue(db_addr in submitted_contacts)
            self.assertTrue(form_addr in list(editors))

    def test_blank_contacts(self):
        """
        A new SAC is created, but blank info in the data doesn't result in the
        creation of Access objects with blank name and email fields.
        """
        # Add eligibility and Auditee Info data to profile
        self.user.profile.entry_form_data = (
            VALID_ELIGIBILITY_DATA | VALID_AUDITEE_INFO_DATA
        )
        self.user.profile.save()

        access_and_submission_data = VALID_ACCESS_AND_SUBMISSION_DATA.copy()
        access_and_submission_data["auditee_contacts_email"].append("")
        access_and_submission_data["auditor_contacts_email"].append("")
        # access_and_submission_data["auditor_contacts_email"].append("y")
        access_and_submission_data["auditee_contacts_fullname"].append("")
        access_and_submission_data["auditor_contacts_fullname"].append("")
        # access_and_submission_data["auditor_contacts_fullname"].append("Y")

        response = self.client.post(
            ACCESS_AND_SUBMISSION_PATH, access_and_submission_data, format="json"
        )
        data = response.json()

        audit = Audit.objects.get(report_id=data["report_id"])

        editors = (
            Access.objects.filter(audit=audit, role="editor")
            .values_list("email", flat=True)
            .order_by("email")
        )
        # There should be three editors: the current user, and c@c.com and d@d.com
        # from VALID_ACCESS_AND_SUBMISSION_DATA, and the appended blank values from
        # 20 lines up should not end up adding anything.
        self.assertEqual(3, len(editors))

    def test_invalid_eligibility_data(self):
        """
        Handle missing data.
        """
        self.user.profile.entry_form_data = (
            VALID_ELIGIBILITY_DATA | VALID_AUDITEE_INFO_DATA
        )
        self.user.profile.save()
        response = self.client.post(ACCESS_AND_SUBMISSION_PATH, {}, format="json")
        data = response.json()
        self.assertEqual(
            data.get("errors", [])["certifying_auditee_contact_email"][0],
            "This field is required.",
        )
        self.assertEqual(
            data.get("errors", [])["certifying_auditor_contact_email"][0],
            "This field is required.",
        )
        self.assertEqual(
            data.get("errors", [])["auditee_contacts_email"][0],
            "This field is required.",
        )
        self.assertEqual(
            data.get("errors", [])["auditor_contacts_email"][0],
            "This field is required.",
        )


class SACCreationTests(TestCase):
    """Integration tests covering all submission steps leading up to and including creation of a SingleAuditChecklist instance"""

    def setUp(self):
        self.user = baker.make(User)
        self.client = APIClient()

    def test_valid_data_across_steps_creates_an_sac(self):
        """Upon submitting valid data and following `next` responses, a new SAC is created"""
        self.client.force_authenticate(user=self.user)

        # Submit eligibility data
        eligibility_info = {
            "is_usa_based": True,
            "met_spending_threshold": True,
            "user_provided_organization_type": "state",
        }
        response = self.client.post(ELIGIBILITY_PATH, eligibility_info, format="json")
        data = response.json()
        next_step = data["next"]

        # Submit auditee info
        response = self.client.post(next_step, VALID_AUDITEE_INFO_DATA, format="json")
        data = response.json()
        next_step = data["next"]

        # Submit AccessAndSubmission details
        access_and_submission_data = {
            "certifying_auditee_contact_fullname": "Name",
            "certifying_auditee_contact_email": "a@a.com",
            "certifying_auditor_contact_fullname": "Name",
            "certifying_auditor_contact_email": "b@b.com",
            "auditor_contacts_fullname": ["Name"],
            "auditor_contacts_email": ["c@c.com"],
            "auditee_contacts_fullname": ["Name"],
            "auditee_contacts_email": ["e@e.com"],
        }
        response = self.client.post(
            next_step, access_and_submission_data, format="json"
        )
        data = response.json()
        audit = Audit.objects.get(report_id=data["report_id"])
        self.assertEqual(audit.created_by, self.user)
        self.assertEqual(
            audit.audit.get("general_information", {}).get("auditee_uei", None),
            "ZQGGHJH74DW7",
        )
        self.assertEqual(audit.submission_status, "in_progress")

        # We also need to verify that the response from the POST includes all
        # the fields we expect, including the data that’s actually stored in
        # Access objects related to this Audit instance.


# TODO: Update Post SOC Launch
class SingleAuditChecklistViewTests(TestCase):
    """
    Tests for /sac/edit/[report_id]
    """

    def setUp(self):
        self.user = baker.make(User)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def path(self, report_id):
        """Convenience method to get the path for a report_id)"""
        return reverse("singleauditchecklist", kwargs={"report_id": report_id})

    def test_valid_data_across_steps_is_returned_in_get(self):
        """
        After submitting the valid data and creating an SAC object, we return
        all of the relevant data on GET.
        """
        self.client.force_authenticate(user=self.user)

        # Submit eligibility data
        eligibility_info = {
            "is_usa_based": True,
            "met_spending_threshold": True,
            "user_provided_organization_type": "state",
        }
        response = self.client.post(ELIGIBILITY_PATH, eligibility_info, format="json")
        data = response.json()
        next_step = data["next"]

        # Submit auditee info
        response = self.client.post(next_step, VALID_AUDITEE_INFO_DATA, format="json")
        data = response.json()
        next_step = data["next"]

        # Submit AccessAndSubmission details
        access_and_submission_data = {
            "certifying_auditee_contact_fullname": "Name",
            "certifying_auditee_contact_email": "x@x.com",
            "certifying_auditor_contact_fullname": "Name",
            "certifying_auditor_contact_email": "y@y.com",
            "auditor_contacts_fullname": ["Name"],
            "auditor_contacts_email": ["z@z.com"],
            "auditee_contacts_fullname": ["Name"],
            "auditee_contacts_email": ["yz@yz.com"],
        }
        response = self.client.post(
            next_step, access_and_submission_data, format="json"
        )
        data = response.json()
        audit = Audit.objects.get(report_id=data["report_id"])
        response = self.client.get(self.path(audit.report_id))
        full_data = response.json()
        for key, value in access_and_submission_data.items():
            if key in ["auditee_contacts_email", "auditor_contacts_email"]:
                for item in value:
                    self.assertTrue(item in full_data["editors"])
            elif key in [
                "certifying_auditee_contact_email",
                "certifying_auditor_contact_email",
            ]:
                self.assertEqual(full_data[EMAIL_TO_ROLE[key]], value)
        for key, value in eligibility_info.items():
            self.assertEqual(full_data["general_information"][key], value)
        for key, value in VALID_AUDITEE_INFO_DATA.items():
            self.assertEqual(full_data["general_information"][key], value)

    def test_get_authentication_required(self):
        """
        If a request is not authenticated, it should be rejected with a 403
        DRF's IsAuthenticated permission class returns a 403 instead of a 401, see docs below
        https://www.django-rest-framework.org/api-guide/permissions/#how-permissions-are-determined
        """

        # use a different client that doesn't authenticate
        client = APIClient()

        response = client.get(self.path("test-report-id"), format="json")

        self.assertEqual(response.status_code, 403)

    def test_get_no_audit_access(self):
        """
        If a user doesn't have an Access object for the Audit, they should get a
        403.
        """
        audit = baker.make(Audit, version=0)
        baker.make(SingleAuditChecklist, report_id=audit.report_id)
        response = self.client.get(self.path(audit.report_id))
        self.assertEqual(response.status_code, 403)

    def test_get_audit_access(self):
        """
        If a user has an Access object for the Audit, they should get a 200.
        """
        audit = baker.make(Audit, version=0)
        sac = baker.make(SingleAuditChecklist, report_id=audit.report_id)
        access = baker.make(Access, user=self.user, sac=sac, audit=audit)
        response = self.client.get(self.path(access.audit.report_id))

        self.assertEqual(response.status_code, 200)

    def test_get_bad_report_id(self):
        """
        If the user is logged in and the report ID doesn't match a SAC, they should get a 404.
        """
        response = self.client.get(self.path("nonsensical_id"))

        self.assertEqual(response.status_code, 404)


class SacFederalAwardsViewTests(TestCase):
    """
    Tests for /sac/edit/[report_id]/federal_awards
    """

    def setUp(self):
        self.user = baker.make(User)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Submit eligibility data
        eligibility_info = {
            "is_usa_based": True,
            "met_spending_threshold": True,
            "user_provided_organization_type": "state",
        }
        response = self.client.post(ELIGIBILITY_PATH, eligibility_info, format="json")
        data = response.json()
        next_step = data["next"]

        # Submit auditee info
        response = self.client.post(next_step, VALID_AUDITEE_INFO_DATA, format="json")
        data = response.json()
        next_step = data["next"]

        # Submit AccessAndSubmission details
        response = self.client.post(
            next_step, VALID_ACCESS_AND_SUBMISSION_DATA, format="json"
        )

        # Report details to be used for tests
        self.sac_data = response.json()
        self.sac_report_id = self.sac_data["report_id"]

    def path(self, report_id):
        """Convenience method to get the path for a report_id)"""
        return reverse("sacfederalawards", kwargs={"report_id": report_id})

    def test_get_authentication_required(self):
        """
        If a request is not authenticated, it should be rejected with a 403
        DRF's IsAuthenticated permission class returns a 403 instead of a 401, see docs below
        https://www.django-rest-framework.org/api-guide/permissions/#how-permissions-are-determined
        """

        # use a different client that doesn't authenticate
        client = APIClient()
        response = client.get(self.path(self.sac_report_id), format="json")
        self.assertEqual(response.status_code, 403)

    def test_get_no_audit_awards_access(self):
        """
        If a user doesn't have an Access object for the Audit, they should get a
        403.
        """

        audit = baker.make(Audit, version=0)
        baker.make(SingleAuditChecklist, report_id=audit.report_id)
        response = self.client.get(self.path(audit.report_id))
        self.assertEqual(response.status_code, 403)

    def test_get_valid_placeholder_data(self):
        """
        If the federal awards endpoint is hit, (for now) it should return an empty object
        """

        # SAC created in setUp().
        response = self.client.get(self.path(self.sac_report_id))
        data = response.json()
        self.assertEqual(data, {})


class SubmissionsViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_no_submissions_returns_empty_list(self):
        response = self.client.get(SUBMISSIONS_PATH, format="json")
        data = response.json()
        self.assertEqual(data, [])

    def test_user_with_submissions_should_return_expected_data_columns(self):
        self.user.profile.entry_form_data = (
            VALID_ELIGIBILITY_DATA | VALID_AUDITEE_INFO_DATA
        )
        self.user.profile.save()
        self.client.post(
            ACCESS_AND_SUBMISSION_PATH, VALID_ACCESS_AND_SUBMISSION_DATA, format="json"
        )

        response = self.client.get(SUBMISSIONS_PATH, format="json")

        data = response.json()
        self.assertTrue("report_id" in data[0])
        self.assertEqual(
            data[0]["auditee_uei"],
            VALID_AUDITEE_INFO_DATA["auditee_uei"],
        )
        self.assertEqual(
            data[0]["auditee_fiscal_period_end"],
            VALID_AUDITEE_INFO_DATA["auditee_fiscal_period_end"],
        )
        self.assertEqual(
            data[0]["auditee_name"],
            VALID_AUDITEE_INFO_DATA["auditee_name"],
        )
        self.assertEqual(
            len(data[0]),
            5,
        )


class AccessListViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_authentication_required(self):
        """
        If a request is not authenticated, it should be rejected with a 403
        DRF's IsAuthenticated permission class returns a 403 instead of a 401, see docs below
        https://www.django-rest-framework.org/api-guide/permissions/#how-permissions-are-determined
        """

        # use a different client that doesn't authenticate
        client = APIClient()

        response = client.get(ACCESS_LIST_PATH, format="json")

        self.assertEqual(response.status_code, 403)

    def test_no_access_returns_empty_list(self):
        """
        If a user does not have access to any audits, an empty list is returned
        """
        response = self.client.get(ACCESS_LIST_PATH, format="json")
        data = response.json()

        self.assertEqual(data, [])

    def test_single_access_returns_expected(self):
        """
        If a user has acccess to a single audit, only that audit is returned
        """
        audit = baker.make(Audit, version=0)
        access = baker.make(Access, user=self.user, audit=audit)

        response = self.client.get(ACCESS_LIST_PATH, format="json")
        data = response.json()

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["role"], access.role)
        self.assertEqual(data[0]["report_id"], access.audit.report_id)

    def test_multiple_access_returns_expected(self):
        """
        If a user has access to multiple audits, all are returned
        """
        audit_1 = baker.make(Audit, version=0)
        audit_2 = baker.make(Audit, version=0)
        access_1 = baker.make(Access, user=self.user, audit=audit_1)
        access_2 = baker.make(Access, user=self.user, audit=audit_2)

        response = self.client.get(ACCESS_LIST_PATH, format="json")
        data = response.json()

        self.assertEqual(len(data), 2)

        data_1 = next((a for a in data if a["report_id"] == access_1.audit.report_id))

        self.assertEqual(data_1["role"], access_1.role)
        self.assertEqual(data_1["report_id"], access_1.audit.report_id)

        data_2 = next((a for a in data if a["report_id"] == access_2.audit.report_id))

        self.assertEqual(data_2["role"], access_2.role)
        self.assertEqual(data_2["report_id"], access_2.audit.report_id)

    def test_multiple_roles_returns_expected(self):
        """
        If a user has multiple roles for an audit, that audit is returned one time for each role
        """
        audit = baker.make(Audit, version=0)
        baker.make(
            Access, user=self.user, role="certifying_auditee_contact", audit=audit
        )
        baker.make(Access, user=self.user, role="editor", audit=audit)

        response = self.client.get(ACCESS_LIST_PATH, format="json")
        data = response.json()

        self.assertEqual(len(data), 2)

        certifying_auditee_contact_accesses = list(
            filter(lambda a: a["role"] == "certifying_auditee_contact", data)
        )
        self.assertEqual(len(certifying_auditee_contact_accesses), 1)
        self.assertEqual(
            certifying_auditee_contact_accesses[0]["report_id"], audit.report_id
        )

        editor_accesses = list(filter(lambda a: a["role"] == "editor", data))
        self.assertEqual(len(editor_accesses), 1)
        self.assertEqual(editor_accesses[0]["report_id"], audit.report_id)

    def test_deleted_sac_not_returned(self):
        """
        If a user has their Audits deleted, it is no longer returned in their access list
        """
        audit_1 = baker.make(Audit, version=0)
        sac_1 = baker.make(SingleAuditChecklist, report_id=audit_1.report_id)
        access_1 = baker.make(Access, sac=sac_1, audit=audit_1, user=self.user)

        audit_2 = baker.make(Audit, version=0)
        sac_2 = baker.make(SingleAuditChecklist, report_id=audit_2.report_id)
        baker.make(Access, sac=sac_2, audit=audit_2, user=self.user)

        response_1 = self.client.get(ACCESS_LIST_PATH, format="json")
        data_1 = response_1.json()

        # initially we see both in our access list
        self.assertEqual(len(data_1), 2)

        # now delete one access_2
        sac_2.delete()
        audit_2.delete()

        response_2 = self.client.get(ACCESS_LIST_PATH, format="json")
        data_2 = response_2.json()

        # only the one remaining access should come back
        self.assertEqual(len(data_2), 1)
        self.assertEqual(data_2[0]["report_id"], access_1.audit.report_id)

    def test_deleted_access_not_returned(self):
        """
        If a user has their Access deleted, the associated Audit is no longer returned in their access list
        """
        audit = baker.make(Audit, version=0)
        audit_2 = baker.make(Audit, version=0)
        access_1 = baker.make(Access, user=self.user, audit=audit)
        access_2 = baker.make(Access, user=self.user, audit=audit_2)

        response_1 = self.client.get(ACCESS_LIST_PATH, format="json")
        data_1 = response_1.json()

        # initially we see both in our access list
        self.assertEqual(len(data_1), 2)

        # now delete one access_2
        removing_user = baker.make(User)
        access_2.delete(removing_user=removing_user)

        response_2 = self.client.get(ACCESS_LIST_PATH, format="json")
        data_2 = response_2.json()

        # only the one remaining access should come back
        self.assertEqual(len(data_2), 1)
        self.assertEqual(data_2[0]["report_id"], access_1.audit.report_id)


class SchemaViewTests(TestCase):
    def setUp(self):
        self.fiscal_years = [
            "2023",
        ]

        self.schema_types = [
            "metadata",
        ]

        self.client = APIClient()

    def path(self, fiscal_year, schema_type):
        """Convenience method to get the path for a particular year and schema type)"""
        return reverse(
            "schemas", kwargs={"fiscal_year": fiscal_year, "schema_type": schema_type}
        )

    def test_valid_fy_valid_type_returns_schema(self):
        """
        Requests for valid combinations of fiscal_year and type return a schema
        """
        for fiscal_year in self.fiscal_years:
            for schema_type in self.schema_types:
                with self.subTest():
                    url = self.path(fiscal_year, schema_type)
                    response = self.client.get(url)

                    self.assertEqual(response.status_code, 200)

    def test_invalid_fy_returns_404(self):
        """
        Requests for an invalid fiscal_year return a 404
        """
        for schema_type in self.schema_types:
            with self.subTest():
                url = self.path("1899", schema_type)
                response = self.client.get(url)

                self.assertEqual(response.status_code, 404)

    def test_invalid_type_returns_404(self):
        """
        Requests for an invalid type return a 404
        """
        for fiscal_year in self.fiscal_years:
            with self.subTest():
                url = self.path(fiscal_year, "not-a-valid-type")
                response = self.client.get(url)

                self.assertEqual(response.status_code, 404)
