import logging
from django.contrib.auth import get_user_model
from django.db import models
from audit.models.constants import SUBMISSION_EVENT_TYPES

User = get_user_model()

logger = logging.getLogger(__name__)


class SubmissionEvent(models.Model):
    sac = models.ForeignKey("audit.SingleAuditChecklist", on_delete=models.CASCADE)
    # TODO: Update Post SOC Launch
    # setting this temporarily to allow "null" to handle existing rows without audit fields.
    audit = models.ForeignKey("audit.Audit", on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    event = models.CharField(choices=SUBMISSION_EVENT_TYPES)
