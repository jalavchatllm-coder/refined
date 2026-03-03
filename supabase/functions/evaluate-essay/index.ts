import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Максимальные размеры для валидации
const MAX_ESSAY_LENGTH = 30000; // символов
const MAX_SOURCE_LENGTH = 10000; // символов
const MIN_ESSAY_LENGTH = 10; // минимальная длина

Deno.serve(async (req) => {
  // Preflight запрос
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY');
    const rubertUrl = Deno.env.get('RUBERT_URL');

    if (!supabaseUrl || !supabaseAnonKey) {
      return new Response(JSON.stringify({ error: 'Supabase not configured' }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (!rubertUrl) {
      return new Response(JSON.stringify({ error: 'RUBERT_URL not set in secrets' }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Проверка метода
    if (req.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), {
        status: 405, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Парсинг JSON с ограничением размера
    let body;
    try {
      const text = await req.text();
      if (text.length > 50000) {
        return new Response(JSON.stringify({ error: 'Request too large' }), {
          status: 413, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      body = JSON.parse(text);
    } catch {
      return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Валидация входных данных
    const { essayText, sourceText } = body;
    
    if (!essayText || typeof essayText !== 'string') {
      return new Response(JSON.stringify({ error: 'essayText is required and must be a string' }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (essayText.length < MIN_ESSAY_LENGTH) {
      return new Response(JSON.stringify({ 
        error: `Essay too short. Minimum ${MIN_ESSAY_LENGTH} characters required.` 
      }), {
        status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (essayText.length > MAX_ESSAY_LENGTH) {
      return new Response(JSON.stringify({ 
        error: `Essay too long. Maximum ${MAX_ESSAY_LENGTH} characters allowed.` 
      }), {
        status: 413, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    if (sourceText && (typeof sourceText !== 'string' || sourceText.length > MAX_SOURCE_LENGTH)) {
      return new Response(JSON.stringify({ 
        error: `Source text too long. Maximum ${MAX_SOURCE_LENGTH} characters allowed.` 
      }), {
        status: 413, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Проверка аутентификации (опционально, но рекомендуется)
    const authHeader = req.headers.get('Authorization');
    let user;
    
    if (authHeader) {
      const supabase = createClient(supabaseUrl, supabaseAnonKey, {
        global: { headers: { Authorization: authHeader } }
      });
      
      try {
        const { data: { user: userData }, error } = await supabase.auth.getUser();
        if (!error && userData) {
          user = userData;
        }
      } catch {
        // Пользователь не аутентифицирован - продолжаем без него
      }
    }

    // Вызываем ruBERT сервер
    const response = await fetch(`${rubertUrl}/grade`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        essayText: essayText.trim(), 
        sourceText: sourceText ? sourceText.trim() : '' 
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`ruBERT server error ${response.status}: ${err.substring(0, 200)}`);
    }

    const result = await response.json();

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error: any) {
    console.error('❌ Error:', error?.message);
    return new Response(JSON.stringify({ error: error?.message || 'Internal server error' }), {
      status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
