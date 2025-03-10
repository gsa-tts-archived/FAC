import logging
import math
import textwrap
import time
from datetime import date, timedelta

import newrelic.agent
from config.settings import AGENCY_NAMES, STATE_ABBREVS, SUMMARY_REPORT_DOWNLOAD_LIMIT
from dissemination.file_downloads import get_download_url, get_filename
from dissemination.forms import AdvancedSearchForm, SearchForm
from dissemination.mixins import ReportAccessRequiredMixin
from dissemination.models import (
    AdditionalEin,
    AdditionalUei,
    CapText,
    DisseminationCombined,
    FederalAward,
    Finding,
    FindingText,
    General,
    Note,
    OneTimeAccess,
    SecondaryAuditor,
)
from dissemination.search import gather_errors, search
from dissemination.summary_reports import generate_summary_report
from django.conf import settings
from django.core.exceptions import BadRequest, ValidationError
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from support.decorators import newrelic_timing_metric
from users.permissions import can_read_tribal

logger = logging.getLogger(__name__)

default_checked_audit_years = [
    date.today().year,
    date.today().year - 1,
]  # Auto-check this and last year


def _add_search_params_to_newrelic(search_parameters):
    is_advanced = search_parameters["advanced_search_flag"]
    singles = [
        "start_date",
        "end_date",
        "auditee_state",
    ]

    multis = [
        "uei_or_eins",
        "names",
    ]

    if is_advanced:
        singles.append("cog_or_oversight")
        multis.append("alns")

    newrelic.agent.add_custom_attributes(
        [(f"request.search.{k}", str(search_parameters[k])) for k in singles]
    )

    newrelic.agent.add_custom_attributes(
        [(f"request.search.{k}", ",".join(search_parameters[k])) for k in multis]
    )

    newrelic.agent.add_custom_attribute(
        "request.search.audit_years",
        ",".join([str(ay) for ay in search_parameters["audit_years"]]),
    )


def include_private_results(request):
    """
    Determine if the user is authenicated to see private data.
    """
    if not request.user.is_authenticated:
        return False

    if not can_read_tribal(request.user):
        return False

    return True


def run_search(form_data):
    """
    Given cleaned form data, run the search.
    Returns the results QuerySet.
    """

    basic_parameters = {
        "audit_years": form_data["audit_year"],
        "auditee_state": form_data["auditee_state"],
        "end_date": form_data["end_date"],
        "entity_type": form_data["entity_type"],
        "fy_end_month": form_data["fy_end_month"],
        "names": form_data["entity_name"],
        "report_id": form_data["report_id"],
        "start_date": form_data["start_date"],
        "uei_or_eins": form_data["uei_or_ein"],
        "order_by": form_data["order_by"],
        "order_direction": form_data["order_direction"],
    }
    search_parameters = basic_parameters.copy()

    search_parameters["advanced_search_flag"] = form_data["advanced_search_flag"]
    if search_parameters["advanced_search_flag"]:
        advanced_parameters = {
            "agency_name": form_data["agency_name"],
            "alns": form_data["aln"],
            "cog_or_oversight": form_data["cog_or_oversight"],
            "direct_funding": form_data["direct_funding"],
            "federal_program_name": form_data["federal_program_name"],
            "findings": form_data["findings"],
            "major_program": form_data["major_program"],
            "passthrough_name": form_data["passthrough_name"],
            "type_requirement": form_data["type_requirement"],
        }
        search_parameters.update(advanced_parameters)

    _add_search_params_to_newrelic(search_parameters)

    return search(search_parameters)


# Function to do a dictionary lookup of the agency name to number
def _populate_cog_over_name(results):
    agency_names = AGENCY_NAMES
    for result in results:
        if result.oversight_agency:
            agency_code = result.oversight_agency
            agency_name = agency_names.get(
                result.oversight_agency, result.oversight_agency
            )
            result.agency_name = "\n".join(
                textwrap.wrap(agency_code + " - " + agency_name + " (OVER)", width=20)
            )
        elif result.cognizant_agency:
            agency_code = result.cognizant_agency
            agency_name = agency_names.get(
                result.cognizant_agency, result.cognizant_agency
            )
            result.agency_name = "\n".join(
                textwrap.wrap(agency_code + " - " + agency_name + " (COG)", width=20)
            )
    return results


class AdvancedSearch(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(AdvancedSearch, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        When accessing the search page through get, return the blank search page.
        """
        form = AdvancedSearchForm()

        return render(
            request,
            "search.html",
            {
                "advanced_search_flag": True,
                "form": form,
                "form_user_input": {"audit_year": default_checked_audit_years},
                "state_abbrevs": STATE_ABBREVS,
                "summary_report_download_limit": SUMMARY_REPORT_DOWNLOAD_LIMIT,
            },
        )

    @newrelic_timing_metric("search-advanced")
    def post(self, request, *args, **kwargs):
        """
        When accessing the search page through post, run a search and display the results.
        """
        time_starting_post = time.time()

        form = AdvancedSearchForm(request.POST)
        paginator_results = None
        results_count = None
        page = 1
        results = []
        errors = []
        context = {}

        # Obtain cleaned form data.
        form.is_valid()
        form_data = form.cleaned_data
        form_user_input = {k: v[0] if len(v) == 1 else v for k, v in form.data.lists()}

        # build error list.
        errors = gather_errors(form)

        # Tells the backend we're running advanced search.
        form_data["advanced_search_flag"] = True

        logger.info(f"Advanced searching on fields: {form_data}")

        include_private = include_private_results(request)

        # Generate results on valid user input.
        if form.is_valid():
            results = run_search(form_data)

            results_count = results.count()

            # Reset page to one if the page number surpasses how many pages there actually are
            page = form_data["page"]
            ceiling = math.ceil(results_count / form_data["limit"])
            if not page or page > ceiling or page < 1:
                page = 1

            logger.info(f"TOTAL: results_count: [{results_count}]")

            # The paginator object handles splicing the results to a one-page iterable and calculates which page numbers to show.
            paginator = Paginator(object_list=results, per_page=form_data["limit"])
            paginator_results = paginator.get_page(page)
            paginator_results.adjusted_elided_pages = paginator.get_elided_page_range(
                page, on_each_side=1
            )

        # Reformat dates for pre-populating the USWDS date-picker.
        if form_data.get("start_date"):
            form_user_input["start_date"] = form_data["start_date"].strftime("%Y-%m-%d")
        if form_data.get("end_date"):
            form_user_input["end_date"] = form_data["end_date"].strftime("%Y-%m-%d")

        # populate the agency name in cog/over field
        paginator_results = _populate_cog_over_name(paginator_results)

        context = context | {
            "advanced_search_flag": True,
            "form_user_input": form_user_input,
            "form": form,
            "errors": errors,
            "include_private": include_private,
            "limit": form_data["limit"],
            "order_by": form_data["order_by"],
            "order_direction": form_data["order_direction"],
            "page": page,
            "results_count": results_count,
            "results": paginator_results,
            "state_abbrevs": STATE_ABBREVS,
            "summary_report_download_limit": SUMMARY_REPORT_DOWNLOAD_LIMIT,
        }
        time_beginning_render = time.time()
        total_time_ms = int(
            math.ceil((time_beginning_render - time_starting_post) * 1000)
        )
        total_time_s = total_time_ms / 1000
        logger.info(f"Total time between post and render {total_time_ms}ms")
        return render(request, "search.html", context | {"total_time_s": total_time_s})


class Search(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(Search, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """
        When accessing the search page through get, return the blank search page.
        """
        form = SearchForm()

        return render(
            request,
            "search.html",
            {
                "advanced_search_flag": False,
                "form": form,
                "form_user_input": {"audit_year": default_checked_audit_years},
                "state_abbrevs": STATE_ABBREVS,
                "summary_report_download_limit": SUMMARY_REPORT_DOWNLOAD_LIMIT,
            },
        )

    @newrelic_timing_metric("search")
    def post(self, request, *args, **kwargs):
        """
        When accessing the search page through post, run a search and display the results.
        """
        time_starting_post = time.time()

        form = SearchForm(request.POST)
        paginator_results = None
        results_count = None
        page = 1
        results = []
        errors = []
        context = {}

        # Obtain cleaned form data.
        form.is_valid()
        form_data = form.cleaned_data
        form_user_input = {k: v[0] if len(v) == 1 else v for k, v in form.data.lists()}

        # build error list.
        errors = gather_errors(form)

        # Tells the backend we're running basic search.
        form_data["advanced_search_flag"] = False

        logger.info(f"Searching on fields: {form_data}")

        include_private = include_private_results(request)

        # Generate results on valid user input.
        if form.is_valid():
            results = run_search(form_data)

            results_count = results.count()

            # Reset page to one if the page number surpasses how many pages there actually are
            page = form_data["page"]
            ceiling = math.ceil(results_count / form_data["limit"])
            if not page or page > ceiling or page < 1:
                page = 1

            logger.info(f"TOTAL: results_count: [{results_count}]")

            # The paginator object handles splicing the results to a one-page iterable and calculates which page numbers to show.
            paginator = Paginator(object_list=results, per_page=form_data["limit"])
            paginator_results = paginator.get_page(page)
            paginator_results.adjusted_elided_pages = paginator.get_elided_page_range(
                page, on_each_side=1
            )

        # Reformat dates for pre-populating the USWDS date-picker.
        if form_data.get("start_date"):
            form_user_input["start_date"] = form_data["start_date"].strftime("%Y-%m-%d")
        if form_data.get("end_date"):
            form_user_input["end_date"] = form_data["end_date"].strftime("%Y-%m-%d")

        # populate the agency name in cog/over field
        paginator_results = _populate_cog_over_name(paginator_results)

        context = context | {
            "advanced_search_flag": False,
            "form_user_input": form_user_input,
            "form": form,
            "errors": errors,
            "include_private": include_private,
            "limit": form_data["limit"],
            "order_by": form_data["order_by"],
            "order_direction": form_data["order_direction"],
            "page": page,
            "results_count": results_count,
            "results": paginator_results,
            "state_abbrevs": STATE_ABBREVS,
            "summary_report_download_limit": SUMMARY_REPORT_DOWNLOAD_LIMIT,
        }
        time_beginning_render = time.time()
        total_time_ms = int(
            math.ceil((time_beginning_render - time_starting_post) * 1000)
        )
        total_time_s = total_time_ms / 1000
        logger.info(f"Total time between post and render {total_time_ms}ms")
        return render(request, "search.html", context | {"total_time_s": total_time_s})


class AuditSummaryView(View):
    def get(self, request, report_id):
        """
        Display information about the given report in the dissemination tables.
        1.  See if this audit is available. If not, 404.
        2.  Grab all relevant info from the dissemination tables.
        3.  Wrap the data into a context object for display.
        """
        # Viewable audits __MUST__ be public.
        general = General.objects.filter(report_id=report_id)
        if not general.exists():
            raise Http404(
                "The report with this ID does not exist in the dissemination database."
            )
        general_data = general.values()[0]
        del general_data["id"]

        include_private = include_private_results(request)
        include_private_and_public = include_private or general_data["is_public"]
        data = self.get_audit_content(report_id, include_private_and_public)
        is_sf_sac_downloadable = DisseminationCombined.objects.filter(
            report_id=report_id
        ).exists()

        # Add entity name and UEI to the context, for the footer.
        context = {
            "report_id": report_id,
            "auditee_name": general_data["auditee_name"],
            "auditee_uei": general_data["auditee_uei"],
            "general": general_data,
            "include_private": include_private,
            "data": data,
            "is_sf_sac_downloadable": is_sf_sac_downloadable,
        }

        return render(request, "summary.html", context)

    def get_audit_content(self, report_id, include_private_and_public):
        """
        Grab everything relevant from the dissemination tables.
        Wrap that data into a dict, and return it.
        """
        awards = FederalAward.objects.filter(report_id=report_id)
        audit_findings = (
            Finding.objects.filter(report_id=report_id)
            .order_by("reference_number")
            .distinct("reference_number")
        )
        audit_findings_text = FindingText.objects.filter(report_id=report_id)
        corrective_action_plan = CapText.objects.filter(report_id=report_id)
        notes_to_sefa = Note.objects.filter(report_id=report_id)
        secondary_auditors = SecondaryAuditor.objects.filter(report_id=report_id)
        additional_ueis = AdditionalUei.objects.filter(report_id=report_id)
        additional_eins = AdditionalEin.objects.filter(report_id=report_id)

        data = {}

        # QuerySet values to an array of dicts
        data["Awards"] = [x for x in awards.values()]
        if notes_to_sefa.exists() and include_private_and_public:
            data["Notes to SEFA"] = [x for x in notes_to_sefa.values()]
        if audit_findings.exists():
            data["Audit Findings"] = [x for x in audit_findings.values()]
        if audit_findings_text.exists() and include_private_and_public:
            data["Audit Findings Text"] = [x for x in audit_findings_text.values()]
        if corrective_action_plan.exists() and include_private_and_public:
            data["Corrective Action Plan"] = [
                x for x in corrective_action_plan.values()
            ]
        if secondary_auditors.exists():
            data["Secondary Auditors"] = [x for x in secondary_auditors.values()]
        if additional_ueis.exists():
            data["Additional UEIs"] = [x for x in additional_ueis.values()]
        if additional_eins.exists():
            data["Additional EINs"] = [x for x in additional_eins.values()]

        return data


class PdfDownloadView(ReportAccessRequiredMixin, View):
    def get(self, request, report_id):
        """
        Given a report_id in the URL, find the relevant PDF in S3 and
        redirect to the download link.
        """
        # only allow PDF downloads for disseminated submissions
        get_object_or_404(General, report_id=report_id)

        filename = get_filename(report_id, "report")

        return redirect(get_download_url(filename))


class XlsxDownloadView(ReportAccessRequiredMixin, View):
    def get(self, request, report_id, file_type):
        """
        Given a report_id and workbook section (file_type) in the URL,
        find the relevant XLSX file in S3 and redirect to its download link.
        """
        # only allow xlsx downloads from disseminated submissions
        get_object_or_404(General, report_id=report_id)

        filename = get_filename(report_id, file_type)

        return redirect(get_download_url(filename))


class OneTimeAccessDownloadView(View):
    def get(self, request, uuid):
        """
        Given a one time access UUID:
        - Clear all expired OneTimeAccess objects from the database
        - Query for a OneTimeAccess object with a matching UUID
        - If found
          - Generate an S3 link to the SingleAuditReport PDF associated with the OneTimeAccess object
          - Delete the OneTimeAccess object
          - Redirect to the generated S3 link
        - If not found
          - Return 404
        """
        try:
            # delete all expired OTA objects
            cutoff = timezone.now() - timedelta(
                seconds=settings.ONE_TIME_ACCESS_TTL_SECS
            )
            OneTimeAccess.objects.filter(timestamp__lt=cutoff).delete()

            # try to find matching OTA object
            ota = OneTimeAccess.objects.get(uuid=uuid)

            # get the filename for the SingleAuditReport for this SAC
            filename = get_filename(ota.report_id, "report")
            download_url = get_download_url(filename)

            # delete the OTA object
            ota.delete()

            # redirect the caller to the file download URL
            return redirect(download_url)

        except OneTimeAccess.DoesNotExist:
            raise Http404()
        except ValidationError:
            raise BadRequest()


class SingleSummaryReportDownloadView(View):
    def get(self, request, report_id):
        """
        Given a report_id in the URL, generate the summary report in S3 and
        redirect to its download link.
        """
        sac = get_object_or_404(General, report_id=report_id)
        include_private = include_private_results(request)
        filename, workbook_bytes = generate_summary_report(
            [sac.report_id], include_private
        )

        # Create an HTTP response with the workbook file for download
        response = HttpResponse(
            workbook_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f"attachment; filename={filename}"

        return response


class MultipleSummaryReportDownloadView(View):
    def post(self, request):
        """
        1. Run a fresh search with the provided search parameters
        2. Get the report_id's from the search
        3. Generate a summary report with the report_ids, which goes into into S3
        4. Redirect to the download url of this new report
        """
        form = AdvancedSearchForm(request.POST)

        try:
            if form.is_valid():
                form_data = form.cleaned_data
                form_data["advanced_search_flag"] = True
            else:
                raise ValidationError("Form error in Search POST.")

            include_private = include_private_results(request)
            results = run_search(form_data)
            results = results[:SUMMARY_REPORT_DOWNLOAD_LIMIT]  # Hard limit XLSX size

            if len(results) == 0:
                raise Http404("Cannot generate summary report. No results found.")
            report_ids = [result.report_id for result in results]
            filename, workbook_bytes = generate_summary_report(
                report_ids, include_private
            )
            # Create an HTTP response with the workbook file for download
            response = HttpResponse(
                workbook_bytes,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = f"attachment; filename={filename}"

            return response

        except Http404 as err:
            logger.info(
                "No results found for MultipleSummaryReportDownloadView post. Suggests an improper or old form submission."
            )
            raise Http404 from err
        except Exception as err:
            logger.info(
                "Unexpected error in MultipleSummaryReportDownloadView post:\n%s", err
            )
            raise BadRequest(err)
