import re
import pymorphy3

from reviews.models import SuggestedActionWord

_morph = pymorphy3.MorphAnalyzer()


def extract_actions(text: str) -> tuple[list[str], list[str]]:
    required_actions = []
    potential_actions = []

    if not text:
        return required_actions, potential_actions

    bag_of_words = set(SuggestedActionWord.objects.values_list('word', flat=True))
    words = re.findall(r'\b\w+\b', text.lower())

    for word in words:
        if word in bag_of_words:
            if word not in required_actions:
                required_actions.append(word)
            continue
            
        parsed = _morph.parse(word)
        if not parsed:
            continue
            
        p = parsed[0]
        if 'VERB' in p.tag or 'INFN' in p.tag:
            if 'INFN' in p.tag or 'futr' in p.tag:
                if word not in potential_actions:
                    potential_actions.append(word)

    return required_actions, potential_actions
