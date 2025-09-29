from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Institution(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    address = models.TextField(verbose_name="Адрес")
    yandex_map_link = models.URLField(max_length=500, verbose_name="Ссылка на Yandex Maps")
    gis_map_link = models.URLField(max_length=500, verbose_name="Ссылка на 2GIS")

    class Meta:
        verbose_name = "Учреждение"
        verbose_name_plural = "Учреждения"

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название")
    date = models.DateTimeField(verbose_name="Дата мероприятия")

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"

    def __str__(self):
        return self.name


class Review(models.Model):
    TONE_CHOICES = [
        ("positive", "Положительный"),
        ("negative", "Отрицательный"),
        ("spam", "Спам"),
    ]

    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Учреждение"
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
        verbose_name="Мероприятие"
    )
    text = models.TextField(verbose_name="Текст отзыва")
    sentiment = models.CharField(
        max_length=10,
        choices=TONE_CHOICES,
        null=True,
        verbose_name="Тональность отзыва"
    )
    confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        null=True,
        verbose_name="Уверенность модели",
        help_text="Значение от 0.0 до 1.0"
    )
    keywords = models.JSONField(
        default=list,
        verbose_name="Ключевые слова",
        help_text="Список ключевых слов в формате JSON"
    )
    reviewed_at = models.DateTimeField(verbose_name="Дата написания отзыва")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Отзыв #{self.id} - {self.sentiment}"
