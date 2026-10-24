from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import timedelta
from django.utils import timezone


class User(AbstractUser):
    streak = models.IntegerField(default=0)
    streak_cooldown_until = models.DateTimeField(null=True, blank=True)

    @property
    def is_streak_on_cooldown(self):
        return bool(
            self.streak_cooldown_until
            and timezone.now() < self.streak_cooldown_until
        )

    def append_to_streak(self):
        """Increment the streak only after its 24-hour cooldown has elapsed."""
        if self.is_streak_on_cooldown:
            return False

        self.streak += 1
        self.streak_cooldown_until = timezone.now() + timedelta(hours=24)
        self.save(update_fields=["streak", "streak_cooldown_until"])
        return True

    class Stage(models.TextChoices):
        HIRAGANA = 'HIRAGANA', 'Hiragana Phase'
        KATAKANA = 'KATAKANA', 'Katakana Phase'
        KANJI = 'KANJI', 'First 30 Kanji'
        GRAMMAR = 'GRAMMAR', 'Core Grammar'

    highest_unlocked_stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        default=Stage.HIRAGANA,
    )

    def __str__(self):
        return self.username