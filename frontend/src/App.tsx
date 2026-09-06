/** Shared page shell, language controls, attribution, and the initial client-side routes. */
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, Route, Routes } from 'react-router';
import { Icon } from './components/Icon';
import { changeLanguage } from './i18n';
import { HomePage } from './pages/HomePage';

/** Keep unknown URLs recoverable without presenting an unrelated page as a valid route. */
function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <main id="main-content" className="py-24 min-[850px]:py-25" tabIndex={-1}>
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
        className="skip-link fixed top-3 left-3 z-100 rounded-lg bg-accent px-5 py-3 text-white"
        href="#main-content"
      >
        {t('app.skipToContent')}
      </a>
      <header className="flex min-h-25 items-center justify-between gap-5 border-b border-line">
        <Link
          className="inline-flex items-center gap-2.75 text-[25px] font-[750] tracking-[-1.2px] text-ink no-underline"
          to="/"
          aria-label={t('app.home')}
        >
          <span className="grid size-9.75 place-items-center rounded-xl bg-accent text-paper">
            <Icon name="gadiruta" size={27} />
          </span>
          <span>{t('app.name')}</span>
        </Link>
        <div
          className="flex items-center gap-0.5 text-[13px] font-bold"
          role="group"
          aria-label={t('language.label')}
        >
          <button
            type="button"
            lang="en"
            aria-label={t('language.en')}
            aria-pressed={language === 'en'}
            className={`min-h-11 min-w-11 rounded-lg border-0 bg-transparent px-2 text-muted transition-colors hover:text-ink ${language === 'en' ? 'bg-surface-active text-accent' : ''}`}
            onClick={() => changeLanguage('en')}
          >
            {t('language.enShort')}
          </button>
          <span className="text-muted-faint" aria-hidden="true">
            /
          </span>
          <button
            type="button"
            lang="es"
            aria-label={t('language.es')}
            aria-pressed={language === 'es'}
            className={`min-h-11 min-w-11 rounded-lg border-0 bg-transparent px-2 text-muted transition-colors hover:text-ink ${language === 'es' ? 'bg-surface-active text-accent' : ''}`}
            onClick={() => changeLanguage('es')}
          >
            {t('language.esShort')}
          </button>
        </div>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <footer className="grid gap-4.5 border-t border-line py-6.25 pb-8.75 min-[850px]:grid-cols-[1fr_1.65fr] min-[850px]:items-start min-[850px]:gap-10">
        <p className="text-[13px] font-semibold">{t('footer.region')}</p>
        <div className="max-w-150 text-[11px] leading-[1.7] text-muted">
          <p>
            {t('footer.attribution')}{' '}
            <a
              className="underline decoration-line-decoration underline-offset-[3px] hover:text-accent"
              href="https://api.ctan.es/doc/"
            >
              {t('footer.source')}
            </a>
            .
          </p>
          <p className="mt-1.25">{t('footer.independent')}</p>
        </div>
      </footer>
    </div>
  );
}
