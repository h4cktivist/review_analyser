from djantimat.helpers import RegexpProc


def get_wrapped_prof_words(text: str) -> str:
    return RegexpProc.replace(text, repl='***')
