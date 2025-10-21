from django.db import models
import hashlib


class AnalyzedString(models.Model):
    # Use the SHA-256 hex digest (64 chars) as the primary key.
    id = models.CharField(max_length=64, primary_key=True, editable=False)
    value = models.CharField(max_length=255)
    length = models.IntegerField()
    is_palindrome = models.BooleanField()
    unique_characters = models.IntegerField()
    word_count = models.IntegerField()
    sha256_hash = models.CharField(max_length=64, editable=False)
    character_frequency_map = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Compute SHA-256 from the string value (always use UTF-8)
        if self.value is None:
            computed = ''
        else:
            computed = hashlib.sha256(self.value.encode('utf-8')).hexdigest()

        # Set both fields to the computed digest. Marking them non-editable
        self.sha256_hash = computed
        self.id = computed

        super().save(*args, **kwargs)

    def __str__(self):
        return f"AnalyzedString(id={self.id}, value={self.value})"