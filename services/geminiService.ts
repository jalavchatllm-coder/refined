import { supabase, isSupabaseConfigured } from './supabaseClient';
import type { EvaluationResult } from '../types';

// Helper to get authentication token
const getAuthToken = async (): Promise<string> => {
    // Try method 1: getSession()
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
        return session.access_token;
    }

    // Try method 2: getUser() - works even if session not in memory
    const { data: { user }, error } = await supabase.auth.getUser();
    if (user && !error) {
        // If user exists but no session, try to get session again (it might load now)
        const { data: { session: newSession } } = await supabase.auth.getSession();
        if (newSession?.access_token) {
            return newSession.access_token;
        }
    }

    // Try method 3: Get token from localStorage (fallback for auth state persistence)
    const storageKey = `sb-${import.meta.env.VITE_SUPABASE_URL?.split('/').reverse()[0]}-auth-token`;
    try {
        const stored = localStorage.getItem(storageKey);
        if (stored) {
            const parsed = JSON.parse(stored);
            if (parsed.access_token) {
                return parsed.access_token;
            }
        }
    } catch (e) {
        // localStorage parsing failed, continue
    }

    throw new Error("Not authenticated");
};

// Helper to call Edge Functions with proper authentication
const invokeEdgeFunction = async (functionName: string, body: any) => {
    const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
    if (!supabaseUrl) {
        throw new Error("Supabase URL not configured");
    }

    const url = `${supabaseUrl}/functions/v1/${functionName}`;

    // Получаем токен если есть сессия (необязательно)
    let token: string | null = null;
    try {
        token = await getAuthToken();
    } catch {
        // не авторизован — продолжаем без токена
    }

    const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'apikey': anonKey,
        'Authorization': `Bearer ${token ?? anonKey}`,
    };
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorText = await response.text();
            let errorMessage = errorText;
            try {
                const errorJson = JSON.parse(errorText);
                errorMessage = errorJson.error || errorText;
            } catch {}
            
            throw new Error(`Edge Function error ${response.status}: ${errorMessage}`);
        }

        return await response.json();
    } catch (error: any) {
        if (error.message?.includes('Edge Function error')) {
            throw error;
        }
        throw new Error(`Failed to call ${functionName}: ${error.message}`);
    }
};

export const evaluateEssay = async (essayText: string, sourceText: string): Promise<EvaluationResult> => {
    try {
        // Check if Supabase is configured
        if (!isSupabaseConfigured()) {
            throw new Error("Supabase is not configured. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your .env file.");
        }

        const data = await invokeEdgeFunction('evaluate-essay', { essayText, sourceText });
        return data as EvaluationResult;
    } catch (error: any) {
        const message = error.message || "Unknown error";
        
        throw new Error("Ошибка при проверке сочинения: " + message);
    }
};


export const generateEssay = async (sourceText: string): Promise<{ text: string; sources?: { title: string; uri: string }[] }> => {
    try {
        // Check if Supabase is configured
        if (!isSupabaseConfigured()) {
            throw new Error("Supabase is not configured. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your .env file.");
        }

        const data = await invokeEdgeFunction('generate-essay', { sourceText });
        return data as { text: string; sources?: { title: string; uri: string }[] };
    } catch (error: any) {
        const message = error.message || "Unknown error";
        
        throw new Error("Ошибка при генерации сочинения: " + message);
    }
};
