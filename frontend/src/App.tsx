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
    <main id="main-content" className="not-found" tabIndex={-1}>
      <h1>{t('notFound.title')}</h1>
      <p>{t('notFound.description')}</p>
      <Link className="text-button" to="/">
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
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        {t('app.skipToContent')}
      </a>
      <header className="site-header">
        <Link className="brand" to="/" aria-label={t('app.home')}>
          <span className="brand-mark">
            <Icon name="route" />
          </span>
          <span>{t('app.name')}</span>
        </Link>
        <div className="language-switch" role="group" aria-label={t('language.label')}>
          <button
            type="button"
            lang="en"
            aria-label={t('language.en')}
            aria-pressed={language === 'en'}
            onClick={() => changeLanguage('en')}
          >
            {t('language.enShort')}
          </button>
          <span aria-hidden="true">/</span>
          <button
            type="button"
            lang="es"
            aria-label={t('language.es')}
            aria-pressed={language === 'es'}
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
      <footer className="site-footer">
        <p className="footer-region">{t('footer.region')}</p>
        <div className="footer-source">
          <p>
            {t('footer.attribution')} <a href="https://api.ctan.es/doc/">{t('footer.source')}</a>.
          </p>
          <p>{t('footer.independent')}</p>
        </div>
      </footer>
    </div>
  );
}
