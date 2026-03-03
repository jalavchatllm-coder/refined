import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const authHeader = req.headers.get('Authorization');
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY');

    if (!supabaseUrl || !supabaseAnonKey) {
      throw new Error("Supabase environment variables are missing in Edge Function");
    }

    // Опциональная авторизация
    let supabaseClient = null;
    let user = null;
    let profile = null;

    const token = authHeader?.replace('Bearer ', '');
    const isUserToken = token && token !== supabaseAnonKey;

    if (isUserToken) {
      supabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
        global: { headers: { Authorization: authHeader! } }
      });
      const { data: { user: u } } = await supabaseClient.auth.getUser();
      user = u;
      if (user) {
        const { data: p } = await supabaseClient
          .from('profiles')
          .select('free_checks')
          .eq('id', user.id)
          .single();
        profile = p;
      }
    }

    const { sourceText } = await req.json();
    const apiKey = Deno.env.get('API_KEY');

    if (!apiKey) {
        throw new Error("Missing API_KEY in Edge Function secrets");
    }

    const generationPrompt = `
    Напиши идеальное сочинение ЕГЭ по русскому языку (задание 27) на основе приведенного текста.
    Сочинение должно быть структурным, грамотным и глубоким.
    Объем: 200-300 слов.

    === ИСХОДНЫЙ ТЕКСТ ===
    ${sourceText}
    ======================
    `;

    // Use Gemini API
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            contents: [{ parts: [{ text: generationPrompt }] }]
        })
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Gemini API Error: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    const text = data.candidates?.[0]?.content?.parts?.[0]?.text;

    if (!text) {
         throw new Error("Model returned empty text");
    }


    return new Response(JSON.stringify({ text: text }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error: any) {
    console.error("Edge Function Error:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});