/** Shared page shell, language controls, attribution, and the initial client-side routes. */
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, Route, Routes } from 'react-router';
import { AppFooter } from './components/AppFooter';
import { AppHeader } from './components/AppHeader';
import { HomePage } from './pages/HomePage';

/** Keep unknown URLs recoverable without presenting an unrelated page as a valid route. */
function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <main id="main-content" className="py-24 desktop:py-25" tabIndex={-1}>
      <h1 className="max-w-162.5 text-[clamp(44px,7vw,76px)] leading-[1.05] font-[650] tracking-[-2.8px]">
        {t('notFound.title')}
      </h1>
      <p className="my-6 text-muted">{t('notFound.description')}</p>
      <Link
        className="inline-flex min-h-11 items-center bg-transparent px-1.25 text-sm font-[650] text-accent underline decoration-1 underline-offset-4"
        to="/"
      >
        {t('notFound.back')}
      </Link>
    </main>
  );
}

/** Render the bilingual application and synchronize document metadata with its language. */
export default function App() {
  const { t, i18n } = useTranslation();
  const language = i18n.resolvedLanguage ?? 'en';

  useEffect(() => {
    document.documentElement.lang = language;
    document.title = t('app.title');
  }, [language, t]);

  return (
    <div className="mx-auto w-[calc(100%-40px)] max-w-280 max-[380px]:w-[calc(100%-28px)]">
      <a
        className="skip-link fixed top-3 left-3 z-100 rounded-lg bg-accent px-5 py-3 text-on-accent"
        href="#main-content"
      >
        {t('app.skipToContent')}
      </a>
      <AppHeader />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <AppFooter />
    </div>
  );
}
