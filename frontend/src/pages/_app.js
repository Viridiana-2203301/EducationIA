/**
 * _app.js - Global layout wrapper for all pages.
 */
import '../styles/globals.css';
import Navbar from '../components/Navbar';
import Head from 'next/head';

export default function App({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>CSV Analytics Platform</title>
        <meta name="description" content="Plataforma de análisis automático de múltiples datasets CSV con machine learning" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚡</text></svg>" />
      </Head>
      <div className="app-layout">
        <Navbar />
        <main className="main-content">
          <Component {...pageProps} />
        </main>
      </div>
    </>
  );
}
