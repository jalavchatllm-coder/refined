from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import torch
from transformers import AutoTokenizer, AutoModel
import re
import math

app = FastAPI(title="ЕГЭ Essay Grader", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# ЗАГРУЗКА ruBERT
# ============================================================

MODEL_NAME = "DeepPavlov/rubert-base-cased-sentence"
tokenizer = None
model = None

def load_model():
    global tokenizer, model
    print("Loading ruBERT model...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    model.eval()
    print("ruBERT loaded!")

@app.on_event("startup")
async def startup():
    load_model()

# ============================================================
# УТИЛИТЫ
# ============================================================

def normalize(text: str) -> str:
    return text.lower().replace("ё", "е").strip()

def count_words(text: str) -> int:
    return len([w for w in text.strip().split() if w])

def get_paragraphs(text: str) -> list:
    return [p.strip() for p in re.split(r'\n+', text) if p.strip()]

def get_sentences(text: str) -> list:
    return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]

def get_embedding(text: str) -> torch.Tensor:
    """Получить эмбеддинг текста через ruBERT"""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    # Mean pooling
    token_embeddings = outputs.last_hidden_state
    attention_mask = inputs["attention_mask"]
    mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    embedding = torch.sum(token_embeddings * mask_expanded, 1) / torch.clamp(mask_expanded.sum(1), min=1e-9)
    return embedding[0]

def cosine_similarity(a: torch.Tensor, b: torch.Tensor) -> float:
    return torch.nn.functional.cosine_similarity(a.unsqueeze(0), b.unsqueeze(0)).item()

def sentence_relevance(essay: str, source: str) -> float:
    """Семантическая близость сочинения к исходному тексту"""
    if not source or len(source) < 10:
        return 0.5
    emb_essay = get_embedding(essay[:512])
    emb_source = get_embedding(source[:512])
    return cosine_similarity(emb_essay, emb_source)

# ============================================================
# АНАЛИЗ СТРУКТУРЫ И ПАТТЕРНОВ
# ============================================================

K1_PHRASES = [
    "проблем", "автор поднимает", "автор рассматривает", "автор размышляет",
    "в тексте говорится", "текст посвящен", "автор обращается", "в своем тексте",
    "автор затрагивает", "автор считает", "позиция автора", "автор убежден",
    "автор показывает", "автор раскрывает", "автор исследует", "писатель поднимает",
    "главная мысль", "основная идея", "автор задается вопросом", "автор ставит вопрос",
    "автор хочет донести", "автор стремится", "волнует автора", "беспокоит автора",
    "автор обеспокоен", "тема текста", "центральная тема", "лейтмотив",
]

K2_EXAMPLE_PHRASES = [
    "например", "в частности", "автор пишет", "автор описывает",
    "автор рассказывает", "в тексте", "герой", "персонаж", "рассказчик",
    "автор показывает", "автор замечает", "автор говорит", "автор отмечает",
    "автор приводит", "в произведении", "писатель", "в первом абзаце",
    "во втором абзаце", "в начале текста", "в конце текста", "обратим внимание",
    "автор изображает", "автор акцентирует", "автор подчеркивает",
    "в эпизоде", "сцена", "фрагмент", "строки", "читаем", "автор сообщает",
    "автор констатирует", "можно заметить", "следует отметить",
    # Дополнительные маркеры для лучшего распознавания
    "автор упоминает", "автор фиксирует", "автор наблюдает", "автор видит",
    "мы видим", "мы замечаем", "мы читаем", "мы можем увидеть",
    "об этом говорится", "это видно", "это заметно", "это можно увидеть",
    "в данном тексте", "в этом тексте", "данном эпизоде", "этом фрагменте",
    "цитируя текст", "как пишет автор", "как говорит автор", "как отмечает автор",
    "авторская позиция", "точка зрения автора", "слова автора", "по мнению автора",
]

K2_LINK_PHRASES = [
    "таким образом", "следовательно", "оба примера", "эти примеры",
    "противопоставление", "дополняют", "подтверждают", "кроме того",
    "во-первых", "во-вторых", "с одной стороны", "с другой стороны",
    "не случайно", "именно поэтому", "это объясняет", "данные примеры",
    "оба эпизода", "сравнивая", "противопоставляя", "оба фрагмента",
    "между примерами", "смысловая связь", "причинно-следственная",
    "дополняя друг друга", "в противовес", "по контрасту",
    "оба примера раскрывают", "эти примеры раскрывают", "примеры связаны",
    "вместе эти примеры", "такая связь примеров", "сначала", "затем",
    "с одной стороны", "с другой", "это позволяет сделать вывод",
    "из этого следует", "тем самым",
    # Дополнительные маркеры связи
    "оба примера показывают", "оба примера говорят", "оба примера свидетельствуют",
    "эти примеры показывают", "эти примеры говорят", "эти примеры свидетельствуют",
    "первый пример", "второй пример", "один пример", "другой пример",
    "в первом случае", "во втором случае", "в одном случае", "в другом случае",
    "пример выше", "предыдущий пример", "следующий пример",
    "связь между", "взаимосвязь", "единство", "общее",
    "подтверждает сказанное", "доказывает вышесказанное", "иллюстрирует это",
    "как мы видим", "как было сказано", "как уже отмечалось",
]

K3_OPINION_PHRASES = [
    "я считаю", "я думаю", "я согласен", "я не согласен", "по моему мнению",
    "на мой взгляд", "мне кажется", "я полагаю", "мое мнение", "я убежден",
    "я уверен", "я разделяю", "нельзя не согласиться", "я придерживаюсь",
    "с моей точки зрения", "по-моему", "лично я", "мне представляется",
    "я поддерживаю позицию", "разделяю мнение", "соглашусь с автором",
    "не могу не согласиться", "я отчасти согласен",
    "с позицией автора согласен", "с позицией автора не согласен",
    "позиция автора мне близка", "позиция автора мне понятна",
    "поддерживаю автора", "не разделяю позицию автора",
    "трудно не согласиться с автором", "считаю позицию автора верной",
    "моя позиция", "мое отношение",
    # Дополнительные маркеры для распознавания позиции
    "я полностью согласен", "я полностью поддерживаю", "я солидарен",
    "я не могу согласиться", "я не поддерживаю", "я отвергаю",
    "мне близка позиция", "мне понятна позиция", "мне импонирует позиция",
    "разделяю точку зрения", "поддерживаю точку зрения", "согласен с точкой зрения",
    "считаю правильным", "считаю верным", "считаю ошибочным",
    "моя точка зрения", "моя собственная позиция", "собственное отношение",
    "выражу свое отношение", "выражу свою позицию", "хочу выразить отношение",
    "невозможно не согласиться", "нельзя не поддержать", "следует поддержать",
    "автор прав", "автор справедливо", "автор верно заметил",
]

K3_ARG_PHRASES = [
    "потому что", "так как", "ведь", "поскольку", "это подтверждает",
    "можно привести", "литература", "жизненный опыт", "вспомним",
    "достаточно вспомнить", "в подтверждение", "свидетельствует",
    "доказывает", "в романе", "в повести", "в рассказе", "в произведении",
    "как отмечал", "по словам", "народная мудрость", "история знает",
    "вспоминается", "приходит на память", "жизнь показывает",
    "как писал", "слова", "высказывание", "цитата",
    # Дополнительные маркеры аргументов
    "пример из жизни", "пример из литературы", "пример из истории",
    "обращусь к литературе", "обращусь к истории", "обратимся к опыту",
    "в реальной жизни", "в жизни мы видим", "жизнь подтверждает",
    "в русской литературе", "в мировой литературе", "в классической литературе",
    "писатель показывает", "писатель демонстрирует", "писатель утверждает",
    "герой произведения", "персонаж романа", "персонаж повести",
    "как показывает практика", "практика подтверждает", "опыт подтверждает",
    "это можно увидеть", "это наблюдается", "это заметно",
    "подтверждение этому", "доказательство этому", "свидетельство этому",
    "аргумент в подтверждение", "в качестве аргумента",
    "литературный пример", "исторический пример", "пример из жизни",
    "вспомним произведение", "вспомним роман", "вспомним повесть",
    "как известно", "все знают", "общепризнанно",
]

K3_POSITION_REGEXES = [
    r'(не\s+могу\s+не\s+согласиться|нельзя\s+не\s+согласиться)\s+с\s+автор',
    r'(согласен|не\s+согласен|солидарен|разделяю|поддерживаю)\s+с\s+автор',
    r'(согласна|не\s+согласна)\s+с\s+автор',
    r'полностью\s+(согласен|согласна)\s+с\s+автор',
    r'позици[яюи]\s+автора.{0,40}(близк|верн|справедлив|ошибоч|поддержива)',
    r'(моя|мое)\s+(позиция|отношение)',
    # Дополнительные regex для распознавания позиции
    r'я\s+(полностью\s+)?(согласен|согласна|поддерживаю|разделяю)',
    r'я\s+не\s+(могу\s+)?(согласен|согласна|поддерживаю)',
    r'считаю\s+(что|эту\s+позицию|его\s+позицию)',
    r'мнение\s+автора\s+(мне\s+)?(близк|понятн|интересн)',
    r'автор\s+(прав|справедлив|верн)',
    r'трудно\s+не\s+согласиться',
    r'нельзя\s+не\s+поддержать',
    r'я\s+убежден[а]?\s+в\s+том',
    r'я\s+уверен[а]?\s+в\s+том',
]

K3_ARGUMENT_REGEXES = [
    r'пример\s+из\s+(жизни|литературы|истории)',
    r'обратимся\s+к\s+(литературе|истории)',
    r'это\s+(доказывает|подтверждает|объясняет)',
    r'потому\s+что|так\s+как|поскольку|ведь',
    # Дополнительные regex для распознавания аргументов
    r'в\s+(романе|повести|рассказе|произведении|поэме)',
    r'(литературн|историческ|жизненн)\s+пример',
    r'герой\s+(произведения|романа|повести|рассказа)',
    r'(писатель|автор)\s+(показывает|демонстрирует|утверждает)',
    r'жизнь\s+(показывает|подтверждает|доказывает)',
    r'(подтверждение|доказательство|свидетельство)\s+этому',
    r'вспомним\s+(произведение|роман|повесть|рассказ)',
    r'(как\s+известно|все\s+знают|общепризнанно)',
    r'(практика|опыт)\s+(показывает|подтверждает)',
]

CONCLUSION_PHRASES = [
    "таким образом", "в заключение", "итак", "подводя итог", "следовательно",
    "в итоге", "хочу сказать", "можно сделать вывод", "резюмируя",
    "подведем итог", "обобщая", "завершая", "в конце концов",
    "из всего сказанного", "подводя итоги", "в финале своего сочинения",
]

INTRO_PHRASES = [
    "в тексте", "автор", "проблем", "вопрос", "данный", "в произведении",
    "передо мной", "я прочитал", "предложенный текст",
]

# ============================================================
# ПРОВЕРКА ОРФОГРАФИИ
# ============================================================

ORTHO_ERRORS = [
    (r'\bнезнаю\b', '"не знаю" — пишется раздельно'),
    (r'\bнемогу\b', '"не могу" — пишется раздельно'),
    (r'\bневидел\b', '"не видел" — пишется раздельно'),
    (r'\bнехочу\b', '"не хочу" — пишется раздельно'),
    (r'\bнепонимаю\b', '"не понимаю" — пишется раздельно'),
    (r'\bнеправильно\b', '"неправильно" — пишется слитно (это верно!)'),
    (r'\bвобщем\b', '"в общем" — пишется раздельно'),
    (r'\bвтечении\b', '"в течение" — пишется раздельно'),
    (r'\bвследствии\b', '"вследствие" — без второго "и" на конце'),
    (r'\bпоэтому что\b', '"потому что" — первое слово "потому"'),
    (r'\bтоже самое\b', '"то же самое" — пишется раздельно'),
    (r'\bкакбудто\b', '"как будто" — пишется раздельно'),
    (r'\bтоесть\b', '"то есть" — пишется раздельно'),
    (r'\bненужно\b', '"не нужно" — пишется раздельно'),
    (r'\bвтомчисле\b', '"в том числе" — пишется раздельно'),
    (r'\bнасамом\b', '"на самом" — пишется раздельно'),
    (r'\bнаоборот\b', '"наоборот" — пишется слитно (это верно!)'),
    (r'\bизза\b', '"из-за" — пишется через дефис'),
    (r'\bпотомучто\b', '"потому что" — пишется раздельно'),
    (r'\bпоэтому\b(?!\s)', '"поэтому" — после слова должен быть пробел'),
    (r'\bнемало\b', '"немало" — слитно или раздельно зависит от контекста'),
    (r'\bнесмотря\s+на\s+то\s+что\b', '"несмотря на то что" — "несмотря" пишется слитно'),
]

# ============================================================
# ГРАММАТИЧЕСКИЕ ОШИБКИ
# ============================================================

GRAMMAR_ERRORS = [
    (r'\bсогласно\s+\w+а\b', 'Согласно чему (дат. падеж), а не чего'),
    (r'\bблагодаря\s+\w+а\b', 'Благодаря чему (дат. падеж), а не чего'),
    (r'\bпо приезду\b', 'По приезде (предложный падеж, не "по приезду")'),
    (r'\bпо окончанию\b', 'По окончании (предложный падеж, не "по окончанию")'),
    (r'\bоплатить за\b', 'Оплатить что (без предлога «за»)'),
    (r'\bпридти\b', 'Правильно: прийти (не "придти")'),
    (r'\bложи(те)?\b', 'Правильно: положи/кладите ("ложить" — просторечие)'),
    (r'\bодеть пальто\b', 'Правильно: надеть пальто ("одевать" — кого-то, "надевать" — что-то)'),
    (r'\bвыйти из ситуации\b', 'Правильно: выйти из положения или найти выход из ситуации'),
    (r'\bиграть роль\b(?!.*\bиграть значение\b)', ''),  # правильно
    (r'\bиметь роль\b', 'Правильно: играть роль или иметь значение'),
    (r'\bпредпринять меры\b', 'Правильно: принять меры (не "предпринять")'),
    (r'\bудовлетворять требованиям\b', 'Правильно: удовлетворять требования или отвечать требованиям'),
    (r'\bпоказывает о том\b', 'Показывает то (без предлога «о»)'),
    (r'\bскучаю за\b', 'Правильно: скучаю по (не "скучаю за")'),
    (r'\bсмеяться над собой\b', ''),  # правильно
    (r'\bсмеяться с\b', 'Правильно: смеяться над (не "смеяться с")'),
]

# ============================================================
# КРИТЕРИИ
# ============================================================

def check_k1(essay: str, has_source: bool, relevance: float) -> dict:
    n = normalize(essay)
    found = [p for p in K1_PHRASES if p in n]

    # Бонус от ruBERT: если сочинение семантически близко к источнику
    semantic_bonus = relevance > 0.4

    if has_source:
        if (len(found) >= 1 and semantic_bonus) or len(found) >= 2:
            return {"score": 1, "comment": "Позиция автора сформулирована.", "errors": []}
        elif len(found) >= 1:
            return {"score": 1, "comment": "Позиция автора обозначена.", "errors": []}
        else:
            return {"score": 0, "comment": "Позиция автора не сформулирована.",
                    "errors": [{"text": "Не найдено явной формулировки проблемы исходного текста."}]}
    else:
        if len(found) >= 1:
            return {"score": 1, "comment": "Проблема сформулирована.", "errors": []}
        return {"score": 0, "comment": "Проблема не сформулирована.",
                "errors": [{"text": "Укажите проблему, которую вы рассматриваете."}]}


def check_k2(essay: str, has_source: bool, relevance: float) -> dict:
    n = normalize(essay)
    word_count = count_words(essay)
    errors = []
    paragraphs = get_paragraphs(essay)

    # Считаем предложения-примеры более гибко: по маркерам, словам "пример/эпизод" и цитированию.
    sentences = get_sentences(essay)
    example_sentences = []
    for s in sentences:
        ns = normalize(s)
        has_marker = any(p in ns for p in K2_EXAMPLE_PHRASES)
        has_example_word = re.search(r'\b(пример|эпизод|фрагмент|случай|сцена)\w*\b', ns) is not None
        has_quote = ('«' in s and '»' in s) or ('"' in s)
        # Проверяем наличие слов "автор", "текст", "произведение" в предложении
        has_text_ref = any(word in ns for word in ["автор", "текст", "произведение", "рассказчик", "герой"])
        if has_marker or (has_example_word and (has_text_ref or has_quote)):
            example_sentences.append(s)

    # Дополнительно: ищем предложения, которые могут содержать примеры по контексту
    if len(example_sentences) < 2:
        for s in sentences:
            ns = normalize(s)
            # Проверяем наличие цитат или отсылок к тексту
            has_citation = ('«' in s and '»' in s) or ('"' in s)
            has_text_reference = any(phrase in ns for phrase in [
                "в тексте", "в произведении", "автор пишет", "автор говорит",
                "автор рассказывает", "автор описывает", "автор показывает"
            ])
            # Если есть цитата или отсылка к тексту, и предложение ещё не добавлено
            if (has_citation or has_text_reference) and s not in example_sentences:
                if len(s.split()) > 5:  # Исключаем слишком короткие предложения
                    example_sentences.append(s)

    # Считаем маркеры связи более гибко
    has_link = any(p in n for p in K2_LINK_PHRASES) or re.search(r'во-?первых.*во-?вторых', n) is not None
    if not has_link:
        has_link = (
            any("сначала" in normalize(s) for s in sentences) and
            any("затем" in normalize(s) or "потом" in normalize(s) for s in sentences)
        )
    # Дополнительно: ищем скрытые маркеры связи
    if not has_link:
        link_patterns = [
            r'первый.*второй', r'один.*другой', r'в начале.*в конце',
            r'с одной.*с другой', r'как.*так и', r'не только.*но и'
        ]
        has_link = any(re.search(pat, n) for pat in link_patterns)

    # Считаем маркеры пояснения (пояснение примера)
    explain_markers = [
        "это значит", "это говорит", "это свидетельствует", "этим автор",
        "данный пример", "это показывает", "это подтверждает", "таким образом",
        "то есть", "иными словами", "другими словами", "следовательно",
        "автор хочет сказать", "автор подчеркивает", "автор выражает",
        "это говорит о том", "это свидетельствует о том", "это доказывает",
        "в этом заключается", "смысл этого", "значение этого",
    ]
    has_explanation = any(p in n for p in explain_markers) or re.search(r'этот\s+(пример|эпизод|фрагмент)\s+(показывает|доказывает|подчеркивает)', n) is not None
    if not has_explanation:
        has_explanation = sum(
            1 for s in sentences
            if re.search(r'(это|данный|этот)\s+(пример|эпизод|фрагмент)', normalize(s))
            and re.search(r'(показывает|доказывает|объясняет|подчеркивает|подтверждает)', normalize(s))
        ) >= 1
    
    # Дополнительно: если есть развёрнутые предложения с анализом
    if not has_explanation:
        for s in sentences:
            ns = normalize(s)
            # Ищем предложения с анализом или интерпретацией
            has_analysis = any(word in ns for word in [
                "анализ", "интерпретация", "понимание", "осмысление",
                "раскрывает", "демонстрирует", "иллюстрирует"
            ])
            if has_analysis and len(s.split()) > 8:
                has_explanation = True
                break

    # Без исходного текста: оцениваем по структуре комментария (0..3).
    if not has_source:
        if len(example_sentences) >= 2 and has_link and has_explanation:
            return {"score": 3, "comment": "Комментарий выстроен: два примера, пояснение и связь между ними.", "errors": []}
        if len(example_sentences) >= 2:
            local_errors = []
            if not has_link:
                local_errors.append({"text": "Добавьте смысловую связь между примерами."})
            if not has_explanation:
                local_errors.append({"text": "Добавьте пояснение к каждому примеру."})
            return {"score": 2, "comment": "Есть два примера, но комментарий раскрыт не полностью.", "errors": local_errors}
        if len(example_sentences) >= 1:
            return {"score": 1, "comment": "Приведен только один пример-иллюстрация.", "errors": [{"text": "Нужно минимум два примера с пояснением."}]}
        return {"score": 0, "comment": "Комментарий к позиции автора не обнаружен.", "errors": [{"text": "Добавьте два примера из текста и пояснение к ним."}]}

    # Два примера = минимум 2 предложения с маркерами примеров
    two_examples = len(example_sentences) >= 2
    one_example = len(example_sentences) >= 1

    # 3 балла: 2 примера + пояснение + смысловая связь
    if two_examples and has_link and has_explanation:
        return {"score": 3, "comment": "Два примера-иллюстрации с пояснением и смысловой связью.", "errors": []}

    # 2 балла: 2 примера без связи
    if two_examples:
        if not has_link:
            errors.append({"text": "Не обозначена смысловая связь между примерами (используйте: «таким образом», «кроме того», «оба примера» и т.д.)."})
        if not has_explanation:
            errors.append({"text": "Добавьте пояснение к каждому примеру (что именно он доказывает по проблеме)."})
        return {"score": 2, "comment": "Два примера есть, но комментарий неполный.", "errors": errors}

    # 1 балл: один пример
    if one_example:
        errors.append({"text": "Приведён только один пример-иллюстрация. Нужно два примера с пояснением каждого."})
        return {"score": 1, "comment": "Только один пример из двух необходимых.", "errors": errors}

    # 0 баллов: нет примеров
    errors.append({"text": "Примеры-иллюстрации из текста отсутствуют. Процитируйте или перескажите два эпизода из текста."})
    return {"score": 0, "comment": "Комментарий к позиции автора отсутствует.", "errors": errors}


def check_k3(essay: str) -> dict:
    n = normalize(essay)
    errors = []
    sentences = get_sentences(essay)

    opinions = len([p for p in K3_OPINION_PHRASES if p in n])
    args = len([p for p in K3_ARG_PHRASES if p in n])
    has_position_regex = any(re.search(pat, n) for pat in K3_POSITION_REGEXES)
    has_argument_regex = any(re.search(pat, n) for pat in K3_ARGUMENT_REGEXES)

    # Проверяем наличие литературных аргументов отдельно
    lit_markers = ["в романе", "в повести", "в рассказе", "в поэме", "в произведении",
                   "толстой", "достоевский", "пушкин", "чехов", "тургенев", "булгаков",
                   "некрасов", "гоголь", "лермонтов", "есенин", "маяковский"]
    has_lit_arg = any(m in n for m in lit_markers)
    
    # Проверяем наличие развёрнутых аргументированных предложений
    has_argument_sentence = any(
        any(p in normalize(s) for p in K3_ARG_PHRASES) and len(s.split()) >= 6
        for s in sentences
    )
    
    # Дополнительно: ищем предложения с явным выражением позиции
    has_position_sentence = any(
        any(p in normalize(s) for p in K3_OPINION_PHRASES) and len(s.split()) >= 4
        for s in sentences
    )
    
    # Проверяем наличие имён писателей (даже без явных маркеров)
    author_names = ["толст", "достоевск", "пушкин", "чехов", "тургенев", "булгаков",
                    "некрасов", "гоголь", "лермонтов", "есенин", "маяковский",
                    "шолохов", "пастернак", "набоков", "солженицын", "бунин",
                    "куприн", "гончаров", "островский", "грибоедов", "фет", "тятчев"]
    has_author_name = any(name in n for name in author_names)
    
    # Проверяем наличие слов "аргумент", "доказательство", "подтверждение"
    has_arg_words = any(word in n for word in ["аргумент", "доказательство", "подтверждение", "обоснование"])
    
    has_position = opinions >= 1 or has_position_regex or has_position_sentence
    has_argument = (args >= 1 or has_lit_arg or has_argument_regex or 
                    has_argument_sentence or has_author_name or has_arg_words)

    if has_position and has_argument:
        return {"score": 2, "comment": "Позиция выражена и обоснована аргументами.", "errors": []}
    elif has_position:
        errors.append({"text": "Аргументация слабая — добавьте пример из литературы или жизни."})
        return {"score": 1, "comment": "Позиция выражена, аргументация недостаточна.", "errors": errors}
    else:
        errors.append({"text": "Собственное отношение к проблеме не выражено."})
        return {"score": 0, "comment": "Собственная позиция отсутствует.", "errors": errors}


def check_k4(essay: str) -> dict:
    # Проверяем очевидные фактические ошибки (имена писателей + произведения)
    errors = []
    wrong_facts = [
        (r'толстой.*преступление', 'Преступление и наказание — Достоевский, не Толстой'),
        (r'пушкин.*война и мир', 'Война и мир — Толстой, не Пушкин'),
        (r'чехов.*евгений онегин', 'Евгений Онегин — Пушкин, не Чехов'),
        (r'гоголь.*отцы и дети', 'Отцы и дети — Тургенев, не Гоголь'),
        (r'тургенев.*мертвые души', 'Мёртвые души — Гоголь, не Тургенев'),
    ]
    n = normalize(essay)
    for pat, hint in wrong_facts:
        if re.search(pat, n):
            errors.append({"text": hint})

    if count_words(essay) < 50:
        return {"score": 0, "comment": "Текст слишком короткий.", "errors": [{"text": "Менее 50 слов."}]}
    if errors:
        return {"score": 0, "comment": "Обнаружены фактические ошибки.", "errors": errors}
    return {"score": 1, "comment": "Грубых фактических ошибок не обнаружено.", "errors": []}


def check_k5(essay: str) -> dict:
    paragraphs = get_paragraphs(essay)
    n = normalize(essay)
    word_count = count_words(essay)
    errors = []

    has_intro = len(paragraphs) > 0 and any(p in normalize(paragraphs[0]) for p in INTRO_PHRASES)
    has_conclusion = any(p in n for p in CONCLUSION_PHRASES)
    enough_paragraphs = len(paragraphs) >= 3

    # Проверка абзацного членения
    if not enough_paragraphs:
        errors.append({"text": f"Мало абзацев ({len(paragraphs)}) — нужно минимум 4: вступление, 2 основных, заключение."})
    if not has_conclusion:
        errors.append({"text": "Заключение отсутствует или не обозначено словами-маркерами."})
    if not has_intro:
        errors.append({"text": "Вступление не выделено или не содержит формулировки проблемы."})

    if enough_paragraphs and has_conclusion and has_intro and word_count >= 150:
        return {"score": 2, "comment": "Текст логично выстроен, структура соблюдена.", "errors": []}
    elif enough_paragraphs and (has_conclusion or has_intro):
        return {"score": 1, "comment": "Логика частично соблюдена.", "errors": errors}
    else:
        return {"score": 0, "comment": "Структура нарушена.", "errors": errors}


def check_k6(essay: str) -> dict:
    n = normalize(essay)
    bad_words = [
        "идиот", "тупой", "дурак", "ненавижу", "мразь", "подонок",
        "негодяй", "ублюдок", "придурок", "кретин", "скотина", "тварь",
    ]
    found = [w for w in bad_words if w in n]
    if found:
        return {"score": 0, "comment": "Этические нарушения.", "errors": [{"text": f'Недопустимое слово: "{w}"'} for w in found]}
    return {"score": 1, "comment": "Этические нормы соблюдены.", "errors": []}


def check_k7(essay: str) -> dict:
    errors = []
    for pat, hint in ORTHO_ERRORS:
        if hint and re.search(pat, essay, re.IGNORECASE):
            errors.append({"text": hint})

    if len(errors) == 0: return {"score": 3, "comment": "Орфографических ошибок не обнаружено.", "errors": []}
    if len(errors) == 1: return {"score": 2, "comment": "1 орфографическая ошибка.", "errors": errors}
    if len(errors) <= 3: return {"score": 1, "comment": f"{len(errors)} орфографические ошибки.", "errors": errors}
    return {"score": 0, "comment": "Более 4 орфографических ошибок.", "errors": errors}


def check_k8(essay: str) -> dict:
    errors = []
    if re.search(r'\s,', essay): errors.append({"text": "Пробел перед запятой."})
    if re.search(r'\s\.', essay): errors.append({"text": "Пробел перед точкой."})
    if re.search(r',[^ \n»]', essay): errors.append({"text": "После запятой нужен пробел."})

    sentences = get_sentences(essay)
    long_no_comma = [s for s in sentences if count_words(s) > 12 and ',' not in s]
    if len(long_no_comma) >= 3:
        errors.append({"text": "В длинных предложениях отсутствуют запятые."})

    # Деепричастные обороты без запятых
    if re.search(r'\b(говоря|думая|смотря|читая|работая|идя)\s+\w+', essay) and ',' not in essay[:100]:
        errors.append({"text": "Возможно не выделен деепричастный оборот запятыми."})

    if len(errors) == 0: return {"score": 3, "comment": "Пунктуационных ошибок не обнаружено.", "errors": []}
    if len(errors) == 1: return {"score": 2, "comment": "1 пунктуационная ошибка.", "errors": errors}
    if len(errors) == 2: return {"score": 1, "comment": "2 пунктуационные ошибки.", "errors": errors}
    return {"score": 0, "comment": "Множественные пунктуационные ошибки.", "errors": errors}


def check_k9(essay: str) -> dict:
    errors = []
    for pat, hint in GRAMMAR_ERRORS:
        if hint and re.search(pat, essay, re.IGNORECASE):
            errors.append({"text": hint})

    if len(errors) == 0: return {"score": 3, "comment": "Грамматических ошибок не обнаружено.", "errors": []}
    if len(errors) == 1: return {"score": 2, "comment": "1 грамматическая ошибка.", "errors": errors}
    if len(errors) <= 3: return {"score": 1, "comment": f"{len(errors)} грамматические ошибки.", "errors": errors}
    return {"score": 0, "comment": "Более 3 грамматических ошибок.", "errors": errors}


def check_k10(essay: str) -> dict:
    errors = []
    n = normalize(essay)
    words = [re.sub(r'[^а-яa-z]', '', w) for w in n.split()]
    words = [w for w in words if len(w) > 4]

    # Тавтология рядом стоящих слов
    seen = set()
    for i in range(len(words) - 1):
        if words[i] == words[i + 1] and words[i] not in seen:
            errors.append({"text": f'Тавтология: слово "{words[i]}" повторяется рядом.'})
            seen.add(words[i])

    # Частые повторы одного слова
    from collections import Counter
    freq = Counter(words)
    for word, cnt in freq.items():
        if cnt >= 5 and len(word) > 4:
            errors.append({"text": f'Слово "{word}" повторяется {cnt} раз — используйте синонимы.'})

    # Короткое сочинение
    wc = count_words(essay)
    if wc < 70:
        errors.append({"text": f"Сочинение слишком короткое ({wc} слов, нужно минимум 70)."})

    if len(errors) == 0: return {"score": 3, "comment": "Речевых ошибок не обнаружено.", "errors": []}
    if len(errors) == 1: return {"score": 2, "comment": "Единичные речевые ошибки.", "errors": errors}
    if len(errors) <= 3: return {"score": 1, "comment": "Несколько речевых ошибок.", "errors": errors}
    return {"score": 0, "comment": "Многочисленные речевые ошибки.", "errors": errors}


# ============================================================
# API
# ============================================================

class EssayRequest(BaseModel):
    essayText: str
    sourceText: Optional[str] = ""

class EssayResponse(BaseModel):
    scores: dict
    totalScore: int
    overallFeedback: str
    meta: dict

@app.get("/")
def root():
    return {"status": "ok", "model": MODEL_NAME}

@app.post("/grade", response_model=EssayResponse)
def grade_essay(req: EssayRequest):
    essay = req.essayText.strip()
    source = (req.sourceText or "").strip()

    if len(essay) < 20:
        raise HTTPException(status_code=400, detail="Сочинение слишком короткое")

    has_source = len(source) > 10

    # Семантическая близость через ruBERT
    relevance = sentence_relevance(essay, source) if has_source else 0.5

    # Проверка по критериям
    scores = {
        "K1": check_k1(essay, has_source, relevance),
        "K2": check_k2(essay, has_source, relevance),
        "K3": check_k3(essay),
        "K4": check_k4(essay),
        "K5": check_k5(essay),
        "K6": check_k6(essay),
        "K7": check_k7(essay),
        "K8": check_k8(essay),
        "K9": check_k9(essay),
        "K10": check_k10(essay),
    }

    total = sum(c["score"] for c in scores.values())
    max_score = 22
    pct = round(total / max_score * 100)

    if pct >= 85:
        feedback = f"Отличное сочинение! {total}/{max_score} баллов."
    elif pct >= 65:
        feedback = f"Хорошее сочинение. {total}/{max_score} баллов. Есть небольшие недочёты."
    elif pct >= 45:
        feedback = f"Удовлетворительно. {total}/{max_score} баллов. Необходимо доработать."
    else:
        feedback = f"Требует значительной доработки. {total}/{max_score} баллов."

    if not has_source:
        feedback += " (проверка без исходного текста)"

    # Советы
    tips = []
    if scores["K1"]["score"] == 0: tips.append("Сформулируйте проблему исходного текста.")
    if scores["K2"]["score"] < 2: tips.append("Приведите два примера из текста и укажите смысловую связь.")
    if scores["K3"]["score"] < 2: tips.append("Выразите позицию и подкрепите аргументом из литературы.")
    if scores["K5"]["score"] < 2: tips.append("Разбейте текст на 4 абзаца: вступление, 2 основных, заключение.")
    if count_words(essay) < 150: tips.append(f"Расширьте сочинение (сейчас {count_words(essay)} слов, рекомендуется 150-300).")

    return EssayResponse(
        scores=scores,
        totalScore=total,
        overallFeedback=feedback,
        meta={
            "wordCount": count_words(essay),
            "paragraphCount": len(get_paragraphs(essay)),
            "hasSource": has_source,
            "semanticRelevance": round(relevance, 3),
            "tips": tips,
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
