from celery.result import AsyncResult
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from importer.tasks import (
    import_gis_reviews_task,
    import_ok_reviews_task,
    import_otzovik_reviews_task,
    import_telegram_reviews_task,
    import_vk_reviews_task,
    import_yandex_reviews_task,
)
from reviews.models import Institution


class BaseImportView(APIView):
    task = None

    def get_institution(self, institution_id):
        try:
            return Institution.objects.get(pk=institution_id)
        except Institution.DoesNotExist:
            return None

    def response_not_found(self):
        return Response(
            {"error": "Institution is not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    def response_bad_request(self, message: str):
        return Response(
            {"error": message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def response_task_accepted(self, request, task_result, source_name: str):
        status_path = reverse("import-task-status", kwargs={"task_id": task_result.id})
        return Response(
            {
                "message": f"{source_name} import has been queued",
                "task_id": task_result.id,
                "status_url": request.build_absolute_uri(status_path),
            },
            status=status.HTTP_202_ACCEPTED,
        )


class GISReviews(BaseImportView):
    task = import_gis_reviews_task
    source_name = "2GIS"

    def post(self, request):
        institution = self.get_institution(request.data.get("institution_id"))
        if not institution:
            return self.response_not_found()

        if not institution.gis_map_link:
            return self.response_bad_request("Institution has no GIS link")

        task_result = self.task.delay(institution.id)
        return self.response_task_accepted(request, task_result, self.source_name)


class YandexReviews(BaseImportView):
    task = import_yandex_reviews_task
    source_name = "Яндекс Карты"

    def post(self, request):
        institution = self.get_institution(request.data.get("institution_id"))
        if not institution:
            return self.response_not_found()

        if not institution.yandex_map_link:
            return self.response_bad_request("Institution has no Yandex link")

        task_result = self.task.delay(institution.id)
        return self.response_task_accepted(request, task_result, self.source_name)


class TelegramReviews(BaseImportView):
    task = import_telegram_reviews_task
    source_name = "Telegram"

    def post(self, request):
        institution = self.get_institution(request.data.get("institution_id"))
        if not institution:
            return self.response_not_found()

        if not institution.telegram_link:
            return self.response_bad_request("Institution has no Telegram link")

        task_result = self.task.delay(institution.id)
        return self.response_task_accepted(request, task_result, self.source_name)


class VKReviews(BaseImportView):
    task = import_vk_reviews_task
    source_name = "VK"

    def post(self, request):
        institution = self.get_institution(request.data.get("institution_id"))
        if not institution:
            return self.response_not_found()

        if not institution.vk_link:
            return self.response_bad_request("Institution has no VK link")

        vk_access_token = request.data.get("vk_access_token")
        if not vk_access_token:
            return self.response_bad_request("vk_access_token is required")

        task_result = self.task.delay(institution.id, vk_access_token)
        return self.response_task_accepted(request, task_result, self.source_name)


class OtzovikReviews(BaseImportView):
    task = import_otzovik_reviews_task
    source_name = "Отзовик"

    def post(self, request):
        institution = self.get_institution(request.data.get("institution_id"))
        if not institution:
            return self.response_not_found()

        if not institution.otzovik_link:
            return self.response_bad_request("Institution has no Otzovik link")

        task_result = self.task.delay(institution.id)
        return self.response_task_accepted(request, task_result, self.source_name)


class OKReviews(BaseImportView):
    task = import_ok_reviews_task
    source_name = "Одноклассники"

    def post(self, request):
        institution = self.get_institution(request.data.get("institution_id"))
        if not institution:
            return self.response_not_found()

        if not institution.ok_link:
            return self.response_bad_request("Institution has no OK link")

        task_result = self.task.delay(institution.id)
        return self.response_task_accepted(request, task_result, self.source_name)


class ImportTaskStatusView(APIView):
    def get(self, request, task_id):
        task_result = AsyncResult(task_id)
        payload = {
            "task_id": task_id,
            "state": task_result.state,
        }

        if task_result.state == "SUCCESS":
            payload["result"] = task_result.result
        elif task_result.state == "FAILURE":
            payload["error"] = str(task_result.result)

        return Response(payload, status=status.HTTP_200_OK)
