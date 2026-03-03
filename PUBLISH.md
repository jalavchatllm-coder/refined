# 🚀 ПУБЛИКАЦИЯ REFINED QUILL

**Краткая инструкция для развёртывания**

---

## ✅ Чеклист перед публикацией

- [ ] Все зависимости установлены (`npm install`)
- [ ] `.env` файл создан с ключами Supabase
- [ ] `security-setup.sql` выполнен в Supabase
- [ ] Edge Function развёрнута
- [ ] `npm run build` выполняется без ошибок

---

## 📋 Шаг 1: Supabase

### 1.1 Создайте проект

1. Перейдите на [supabase.com](https://supabase.com)
2. Создайте новый проект
3. Дождитесь готовности

### 1.2 Выполните SQL скрипт

1. Откройте **SQL Editor** в Dashboard
2. Скопируйте содержимое `security-setup.sql`
3. Вставьте и нажмите **Run**

**Проверка:**
```sql
-- Должны создаться таблицы: profiles, evaluations
select table_name from information_schema.tables 
where table_schema = 'public' order by table_name;
```

### 1.3 Установите секрет

```bash
# Через CLI
supabase secrets set RUBERT_URL=https://greeta-ege-essay-grader.hf.space

# Или через Dashboard:
# Edge Functions → Manage Secrets → Add Secret
```

### 1.4 Разверните Edge Function

```bash
cd supabase/functions
supabase functions deploy evaluate-essay
```

---

## 📋 Шаг 2: Локальная проверка

### 2.1 Создайте .env

```bash
cp .env.example .env
```

### 2.2 Заполните ключи

Получите из Supabase Dashboard → Settings → API:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2.3 Запустите dev сервер

```bash
npm install
npm run dev
```

Откройте http://localhost:5000

**Проверьте:**
- [ ] Сайт загружается
- [ ] Авторизация работает
- [ ] Проверка сочинения работает

### 2.4 Production сборка

```bash
npm run build
```

**Проверьте:**
- [ ] Сборка успешна (ошибок нет)
- [ ] `dist/` папка создана

---

## 📋 Шаг 3: GitHub

```bash
git init
git add .
git commit -m "Refined Quill - production ready"
git branch -M main
git remote add origin https://github.com/your-username/refined-quill.git
git push -u origin main
```

**⚠️ Важно:** `.env` не должен быть в git!

---

## 📋 Шаг 4: Vercel

### 4.1 Import проекта

1. Перейдите на [vercel.com](https://vercel.com)
2. Нажмите **New Project**
3. Выберите GitHub репозиторий
4. Нажмите **Import**

### 4.2 Настройте переменные

**Project Settings → Environment Variables:**

```
VITE_SUPABASE_URL = https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY = your-anon-key
```

### 4.3 Deploy

Нажмите **Deploy**

**Готово!** Через 1-2 минуты сайт будет доступен по URL вида:
```
https://refined-quill.vercel.app
```

---

## 🔧 Решение проблем

### "Failed to send a request"

1. Проверьте `RUBERT_URL` в Supabase Secrets
2. Проверьте логи Edge Function в Dashboard

### "Profile not found"

Выполните `security-setup.sql` ещё раз.

### Сборка падает с ошибкой

```bash
npx tsc -b  # Проверка TypeScript
npm run build  # Проверка сборки
```

---

## 📊 После публикации

### Проверьте:

- [ ] Сайт открывается
- [ ] Авторизация работает
- [ ] Проверка сочинений работает
- [ ] История сохраняется

### Логи:

- **Vercel:** Dashboard → Logs
- **Supabase:** Dashboard → Logs
- **Edge Functions:** Dashboard → Edge Functions → Logs

---

## 📞 Поддержка

**Документация:**
- [README.md](./README.md) — основная
- [SECURITY.md](./SECURITY.md) — безопасность

**Команды:**
```bash
npm run dev      # Dev сервер
npm run build    # Сборка
npx tsc -b       # TypeScript проверка
```

---

**Готово! Сайт опубликован! 🎉**
