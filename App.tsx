import React, { useState, useEffect } from 'react';
import type { Session } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from './services/supabaseClient';
import Loader from './components/Loader';
import AppHeader from './components/AppHeader';
import Statistics from './components/Statistics';
import EssayChecker from './components/EssayChecker';
import Dashboard from './components/Dashboard';
import Auth from './components/Auth';

export type ViewState = 'checker' | 'stats' | 'dashboard' | 'auth';

const App: React.FC = () => {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<ViewState>('checker');

  const handleSignOut = async () => {
    if (isSupabaseConfigured()) {
      await supabase.auth.signOut();
    }
    setSession(null);
    setView('checker');
  };

  useEffect(() => {
    if (isSupabaseConfigured()) {
        supabase.auth.getSession().then(({ data }) => {
            setSession(data?.session ?? null);
            setLoading(false);
        });

        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
        });

        return () => subscription.unsubscribe();
    } else {
        setLoading(false);
    }
  }, []);

  if (loading) {
    return <div className="min-h-screen flex justify-center items-center bg-refined-paper"><Loader /></div>;
  }

  return (
    <div className="min-h-screen bg-refined-paper text-refined-dark font-sans flex flex-col items-center relative overflow-x-hidden selection:bg-refined-red/20 selection:text-refined-dark">
      <div className="absolute top-0 left-0 w-full h-[600px] bg-gradient-to-b from-white to-transparent opacity-60 pointer-events-none z-0"></div>

      <main className="w-full max-w-7xl mx-auto z-10 relative flex-grow flex flex-col px-4 md:px-8 py-6">
        <AppHeader session={session} view={view} setView={setView} onSignOut={handleSignOut} />
        <div className="flex-grow fade-in-section">
            {(() => {
                switch (view) {
                case 'stats':
                    return <Statistics session={session} />;
                case 'dashboard':
                    return <Dashboard session={session} />;
                case 'auth':
                    return <Auth session={session} setView={setView} />;
                case 'checker':
                default:
                    return <EssayChecker session={session} />;
                }
            })()}
        </div>
      </main>
      <footer className="w-full py-6 text-center text-stone-400 text-sm z-10 print:hidden">
        &copy; {new Date().getFullYear()} Refined Quill. Искусство Слова.
      </footer>
    </div>
  );
};

export default App;
