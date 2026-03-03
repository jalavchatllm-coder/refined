import React, { useState } from 'react';
import type { Session } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from '../services/supabaseClient';
import Loader from './Loader';
import type { ViewState } from '../App';

interface AuthProps {
    session: Session | null;
    setView: (view: ViewState) => void;
}

const Auth: React.FC<AuthProps> = ({ setView }) => {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleAuthSuccess = () => {
    setView('dashboard');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!isSupabaseConfigured()) {
        setError('Ошибка подключения к базе данных.');
        return;
    }

    if (!email || !password) {
      setError('Пожалуйста, введите данные.');
      return;
    }

    try {
      setLoading(true);
      if (mode === 'signup') {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        if (data.user && !data.session) {
          setMessage('Инструкции отправлены на ваш email. Проверьте почту для подтверждения.');
          setMode('login');
        } else if (data.session) {
            handleAuthSuccess();
        }
      } else {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        if (data.session) {
            handleAuthSuccess();
        }
      }
    } catch (error: any) {
      setError(error.message || "Ошибка авторизации.");
    } finally {
      setLoading(false);
    }
  };

  return (
     <div className="w-full flex justify-center items-center py-10">
        <div className="w-full max-w-md bg-white p-10 rounded-[2rem] border border-stone-200 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-refined-red/5 rounded-full pointer-events-none -translate-y-1/2 translate-x-1/2"></div>

          {message ? (
            <div className="text-center space-y-4 animate-fade-in relative z-10">
              <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
              </div>
              <h2 className="text-2xl font-serif font-bold text-refined-dark">Проверьте почту</h2>
              <p className="text-stone-500">{message}</p>
              <button onClick={() => { setMessage(''); setLoading(false); }} className="mt-4 text-refined-red hover:text-red-800 font-medium">
                  Вернуться
              </button>
            </div>
          ) : (
            <div className="space-y-8 animate-fade-in relative z-10">
              <div className="text-center">
                  <h2 className="text-3xl font-serif font-bold text-refined-dark mb-2">
                    {mode === 'login' ? 'С возвращением' : 'Регистрация'}
                  </h2>
                  <p className="text-stone-500">Войдите, чтобы сохранять историю проверок.</p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-5">
                  <input
                      className="w-full p-4 bg-stone-50 border border-stone-200 rounded-xl focus:border-refined-red/50 focus:ring-1 focus:ring-refined-red/50 transition-all"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Email"
                      disabled={loading}
                  />
                  <input
                      className="w-full p-4 bg-stone-50 border border-stone-200 rounded-xl focus:border-refined-red/50 focus:ring-1 focus:ring-refined-red/50 transition-all"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Пароль"
                      disabled={loading}
                  />
                  <button type="submit" disabled={loading} className="w-full py-3 bg-refined-red text-white font-bold text-lg rounded-xl hover:bg-red-700 transition-all">
                      {loading ? <Loader /> : (mode === 'login' ? 'Войти' : 'Создать аккаунт')}
                  </button>
              </form>
              {error && <p className="text-red-600 text-sm text-center bg-red-50 p-3 rounded-xl border border-red-100">{error}</p>}
              <div className="text-center">
                  <button onClick={() => setMode(m => m === 'login' ? 'signup' : 'login')} className="text-sm">
                      {mode === 'login' ? 'Нет аккаунта? ' : 'Уже есть аккаунт? '}
                      <span className="text-refined-red font-bold underline">{mode === 'login' ? 'Создать' : 'Войти'}</span>
                  </button>
              </div>
            </div>
          )}
        </div>
     </div>
  );
};

export default Auth;
