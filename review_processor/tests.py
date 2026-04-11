from django.test import TestCase

from reviews.models import SuggestedActionWord

from .action_extractor import extract_actions


class ExtractActionsTests(TestCase):
    def test_empty_or_whitespace_text(self):
        self.assertEqual(extract_actions(""), ([], []))
        self.assertEqual(extract_actions("   "), ([], []))

    def test_word_from_suggested_bag_goes_to_required(self):
        SuggestedActionWord.objects.create(word="тест")
        required, potential = extract_actions("Нужно упомянуть тест отдельно")
        self.assertIn("тест", required)
        self.assertIsInstance(potential, list)
