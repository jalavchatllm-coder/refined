# 🪶 Refined Quill

**Интеллектуальная проверка сочинений ЕГЭ по русскому языку (задание 27)**

Веб-приложение для автоматической проверки сочинений с использованием AI на основе ruBERT.

---

## ✨ Возможности

- ⚡ **Мгновенная проверка** по критериям ФИПИ (К1-К10)
- 🧠 **AI-анализ** через ruBERT (Hugging Face Spaces)
- 📝 **Загрузка .docx** файлов напрямую из Word
- 📊 **История проверок** с сохранением результатов
- 🔒 **Безопасность** — RLS, валидация, защита от XSS/CSRF
- 🎨 **Современный UI** с адаптивным дизайном
- 📱 **Полная поддержка** мобильных устройств

---

## 🚀 Быстрый старт

### Локальная разработка

```bash
# Установите зависимости
npm install

# Запустите dev сервер
npm run dev

# Откройте http://localhost:5000
```

### Production сборка

```bash
# Соберите проект
npm run build

# Превью собранной версии
npm run preview
```

---

## 📋 Требования

- **Node.js** 18+ 
- **Supabase** проект (для авторизации и истории)
- **RuBERT API** (Hugging Face Spaces — уже настроен)

---

## ⚙️ Настройка

### 1. Переменные окружения

Создайте `.env` файл:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

**Получить ключи:** [Supabase Dashboard](https://supabase.com/dashboard)

### 2. Настройка Supabase

**Выполните SQL скрипт:**

1. Откройте [SQL Editor](https://supabase.com/dashboard/project/_/sql/new)
2. Скопируйте `security-setup.sql`
3. Нажмите **Run**

**Установите секрет для Edge Functions:**

```bash
supabase secrets set RUBERT_URL=https://greeta-ege-essay-grader.hf.space
```

### 3. Развёртывание Edge Functions

```bash
# Разверните функцию проверки
supabase functions deploy evaluate-essay
```

---

## 🌐 Публикация

### Vercel (рекомендуется)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-repo/refined-quill)

**Вручную:**

1. Push в GitHub
2. Import в [Vercel](https://vercel.com)
3. Добавьте переменные окружения
4. Deploy

**Environment Variables в Vercel:**
```
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
```

---

## 📁 Структура проекта

```
refined/
├── components/           # React компоненты
│   ├── AppHeader.tsx
│   ├── Auth.tsx
│   ├── Dashboard.tsx
│   ├── EssayChecker.tsx
│   ├── EvaluationDisplay.tsx
│   └── ...
├── services/            # API сервисы
│   ├── supabaseClient.ts
│   └── geminiService.ts
├── supabase/
│   └── functions/
│       └── evaluate-essay/
│           └── index.ts
├── rubert-server/       # RuBERT API (Python/FastAPI)
├── .env.example         # Шаблон переменных
├── security-setup.sql   # SQL для RLS
├── SECURITY.md          # Руководство по безопасности
└── vite.config.ts       # Конфиг Vite
```

---

## 🔒 Безопасность

Проект включает полный набор мер безопасности:

- ✅ **RLS (Row Level Security)** — доступ только к своим данным
- ✅ **Валидация данных** — на клиенте и сервере
- ✅ **XSS защита** — автоматическое экранирование
- ✅ **CSRF защита** — JWT токены
- ✅ **Ограничение запросов** — макс. размер, частота

**Подробности:** [SECURITY.md](./SECURITY.md)

---

## 🛠️ Технологический стек

| Компонент | Технология |
|-----------|-----------|
| Frontend | React 18 + TypeScript |
| Build | Vite |
| UI | Tailwind CSS |
| Auth/DB | Supabase |
| AI | ruBERT (Hugging Face) |
| Hosting | Vercel |

---

## 📚 Документация

| Файл | Описание |
|------|----------|
| [README.md](./README.md) | Этот файл |
| [SECURITY.md](./SECURITY.md) | Руководство по безопасности |
| [SECURITY_AUDIT.md](./SECURITY_AUDIT.md) | Отчёт о проверке безопасности |
| [.env.example](./.env.example) | Шаблон переменных окружения |

---

## 🔧 Скрипты

```bash
npm run dev      # Dev сервер (http://localhost:5000)
npm run build    # Production сборка
npm run preview  # Превью сборки
npm run lint     # Проверка ESLint
```

---

## 📝 Критерии проверки

Приложение проверяет сочинение по 10 критериям ФИПИ:

| Критерий | Баллы | Описание |
|----------|-------|----------|
| К1 | 1 | Проблема текста |
| К2 | 3 | Комментарий |
| К3 | 2 | Собственная позиция |
| К4 | 1 | Фактические ошибки |
| К5-К10 | 14 | Грамотность |
| **Итого** | **22** | Максимальный балл |

---

## 🐛 Решение проблем

### "Failed to send a request"

1. Проверьте, что Edge Functions развёрнуты
2. Установлен ли секрет `RUBERT_URL`?
3. Проверьте логи в Supabase Dashboard

### "Profile not found"

Выполните `security-setup.sql` для создания таблиц.

### Ошибки TypeScript

```bash
npx tsc -b  # Проверка компиляции
```

---

## 🤝 Вклад

1. Fork репозиторий
2. Создайте ветку (`git checkout -b feature/amazing`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing`)
5. Pull Request

---

## 📄 Лицензия

MIT License

---

## 👨‍💻 Автор

Сделано с ❤️ для подготовки к ЕГЭ по русскому языку.

---

**Последнее обновление:** Март 2026  
**Статус:** ✅ Готово к публикации
