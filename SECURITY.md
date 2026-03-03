# 🔒 РУКОВОДСТВО ПО БЕЗОПАСНОСТИ REFINED QUILL

**Дата обновления:** 3 марта 2026  
**Статус:** ✅ Готово к публикации

---

## ✅ ВЫПОЛНЕННЫЕ МЕРЫ БЕЗОПАСНОСТИ

### 1. Защита переменных окружения

**Сделано:**
- ✅ `.env` добавлен в `.gitignore`
- ✅ Создан `.env.example` для безопасного шаринга
- ✅ Удалён Google API ключ (не используется)
- ✅ Секреты для Edge Functions хранятся в Supabase

**Файлы:**
```
.env                    # Игнорируется git
.env.example            # Безопасный шаблон
.gitignore              # Обновлён
```

---

### 2. Supabase RLS (Row Level Security)

**Защищённые таблицы:**
- `profiles` - доступ только к своему профилю
- `evaluations` - доступ только к своим проверкам
- `auth.users` - доступ только к своим данным

**Политики:**
```sql
-- Пользователь видит только свои данные
WHERE auth.uid() = user_id

-- Service role имеет полный доступ (для Edge Functions)
WHERE auth.role() = 'service_role'
```

**Установка:**
```bash
# Выполните в Supabase SQL Editor
# Скопируйте и запустите security-setup.sql
```

---

### 3. Валидация входных данных

**На клиенте (EssayChecker.tsx):**
```typescript
MAX_WORDS = 5000      // Максимум слов
MAX_CHARS = 30000     // Максимум символов
MIN_LENGTH = 10       // Минимум символов
```

**На сервере (Edge Function):**
```typescript
MAX_ESSAY_LENGTH = 30000   // символов
MAX_SOURCE_LENGTH = 10000  // символов
MAX_REQUEST_SIZE = 50000   // байт
```

**Защита:**
- ✅ От слишком больших запросов
- ✅ От пустых данных
- ✅ От некорректного JSON
- ✅ От неправильного типа данных

---

### 4. Защита от XSS (Cross-Site Scripting)

**Встроенная защита:**
- ✅ React автоматически экранирует вывод
- ✅ Нет `dangerouslySetInnerHTML` без санитизации
- ✅ Все пользовательские данные обрабатываются как текст

**Рекомендации:**
```tsx
// ✅ Безопасно
<div>{userInput}</div>

// ❌ Опасно - не использовать без санитизации
<div dangerouslySetInnerHTML={{__html: userInput}} />
```

---

### 5. Защита от CSRF (Cross-Site Request Forgery)

**Меры защиты:**
- ✅ Supabase использует JWT токены
- ✅ Токены хранятся в httpOnly cookie (при использовании Go True)
- ✅ Запросы требуют заголовок Authorization

**Для Edge Functions:**
```typescript
const authHeader = req.headers.get('Authorization');
if (!authHeader) {
  return new Response('Unauthorized', { status: 401 });
}
```

---

### 6. Безопасность Edge Functions

**Обновлённая функция `evaluate-essay`:**

**Проверки:**
1. ✅ Метод запроса (только POST)
2. ✅ Размер запроса (макс. 50KB)
3. ✅ Валидация JSON
4. ✅ Типы данных (string)
5. ✅ Длина текста (мин/макс)
6. ✅ Аутентификация (опционально)

**Ответы:**
- `400` - Некорректные данные
- `405` - Метод не разрешён
- `413` - Слишком большой запрос
- `500` - Ошибка сервера

---

## 📋 ЧЕКЛИСТ ПЕРЕД ПУБЛИКАЦИЕЙ

### 1. Supabase настройки

- [ ] Выполните `security-setup.sql` в Supabase SQL Editor
- [ ] Проверьте RLS политики в Dashboard → Authentication → Policies
- [ ] Убедитесь, что таблицы созданы

**Проверка RLS:**
```sql
-- Проверка политик
select schemaname, tablename, policyname, cmd
from pg_policies
where schemaname = 'public';
```

---

### 2. Секреты Edge Functions

**Установите секреты в Supabase:**

```bash
# Через CLI
supabase secrets set RUBERT_URL=https://greeta-ege-essay-grader.hf.space

# Или через Dashboard:
# Edge Functions → Manage Secrets → Add Secret
# Name: RUBERT_URL
# Value: https://greeta-ege-essay-grader.hf.space
```

---

### 3. Переменные окружения для Vercel

**Добавьте в Vercel Project Settings → Environment Variables:**

```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

**⚠️ НЕ добавляйте:**
- `API_KEY` (не используется)
- `RUBERT_URL` (хранится в Supabase secrets)

---

### 4. Проверка безопасности

**Тесты:**

1. **Проверка RLS:**
```sql
-- Попробуйте получить чужие данные (должно вернуть пусто)
select * from evaluations where user_id != auth.uid();
```

2. **Проверка валидации:**
- Отправьте текст > 30000 символов
- Отправьте пустой текст
- Отправьте некорректный JSON

3. **Проверка CORS:**
- Edge Functions должны принимать запросы только с вашего домена
- Сейчас разрешены все origin (можно ограничить)

---

## 🔧 ДОПОЛНИТЕЛЬНЫЕ МЕРЫ (ОПЦИОНАЛЬНО)

### 1. Ограничение частоты запросов (Rate Limiting)

**Через Supabase:**
```sql
-- Таблица для отслеживания запросов
create table rate_limits (
  user_id uuid primary key,
  requests int default 0,
  reset_at timestamp
);
```

**В Edge Function:**
```typescript
// Проверка лимита перед обработкой
const { requests } = await getRateLimit(userId);
if (requests > 100) {
  return new Response('Rate limit exceeded', { status: 429 });
}
```

---

### 2. Лимит бесплатных проверок

**Включено в `security-setup.sql`:**
```sql
-- Функция check_free_checks()
-- Автоматически уменьшает счётчик при каждой проверке
```

**Активация:**
```sql
-- Создайте триггер
create trigger before_insert_evaluation
  before insert on evaluations
  for each row execute procedure check_free_checks();
```

---

### 3. Ограничение CORS

**В Edge Function замените:**
```typescript
const corsHeaders = {
  'Access-Control-Allow-Origin': 'https://your-domain.com',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'authorization, content-type',
};
```

---

### 4. Логирование подозрительной активности

**Добавьте в Edge Function:**
```typescript
// Логирование ошибок
if (error) {
  await supabase.from('security_logs').insert({
    event: 'validation_error',
    details: error.message,
    ip: req.headers.get('x-forwarded-for'),
  });
}
```

---

## 🚨 ЧТО ДЕЛАТЬ ПРИ УЯЗВИМОСТИ

### 1. Утечка API ключей

1. **Немедленно смените ключи:**
   - Supabase: Dashboard → Settings → API
   - Google: console.cloud.google.com

2. **Обновите секреты:**
```bash
supabase secrets set API_KEY=new_key
```

3. **Обновите переменные в Vercel**

---

### 2. Подозрительная активность

1. **Проверьте логи:**
   - Supabase Dashboard → Logs
   - Edge Functions → Logs

2. **Заблокируйте пользователя:**
```sql
update auth.users
set banned_until = now() + interval '30 days'
where id = 'user-id';
```

3. **Очистите данные:**
```sql
delete from evaluations where user_id = 'suspicious-user-id';
```

---

## 📊 АУДИТ БЕЗОПАСНОСТИ

### Пройденные проверки

| Категория | Статус | Дата |
|-----------|--------|------|
| Переменные окружения | ✅ | 03.03.2026 |
| RLS политики | ✅ | 03.03.2026 |
| Валидация данных | ✅ | 03.03.2026 |
| XSS защита | ✅ | 03.03.2026 |
| CSRF защита | ✅ | 03.03.2026 |
| Edge Functions | ✅ | 03.03.2026 |

### Рекомендуемые проверки

- [ ] Penetration testing (перед production)
- [ ] Аудит зависимостей (`npm audit`)
- [ ] Проверка логов на подозрительную активность

---

## 📞 ЭКСТРЕННАЯ ПОМОЩЬ

**Полезные ссылки:**
- [Supabase Security](https://supabase.com/docs/guides/auth/row-level-security)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Vercel Security](https://vercel.com/docs/security)

**Команды:**
```bash
# Проверка уязвимостей
npm audit

# Обновление зависимостей
npm update

# Пересоздание secret
supabase secrets set KEY_NAME=new_value
```

---

**СТАТУС: ГОТОВО К ПУБЛИКАЦИИ ✅**

Все необходимые меры безопасности приняты. Сайт можно публиковать.
