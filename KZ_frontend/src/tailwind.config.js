/**
 * Knowledge Zakat — Tailwind configuration.
 *
 * Maps the design tokens defined in styles/tokens.css onto Tailwind
 * utility classes. After this, classes like `bg-brand`, `text-brand`,
 * `rounded-card`, `border-kz`, `shadow-brand` work app-wide and
 * automatically pick up the CSS variable values — meaning a single
 * theme change in tokens.css cascades through every page.
 *
 * Note: We deliberately keep Tailwind's built-in `blue-*`, `green-*`,
 * `red-*`, `amber-*` ramps intact so existing pages that reference
 * them (e.g. `bg-blue-100`) keep working during the migration.
 */

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{svelte,js,ts}'],
  theme: {
    extend: {
      // Semantic color aliases — work alongside the default Tailwind palette.
      colors: {
        brand: {
          DEFAULT: 'var(--kz-brand)',         // Navy 900
          50:  'var(--kz-brand-50)',
          100: 'var(--kz-brand-100)',
          200: 'var(--kz-brand-200)',
          300: 'var(--kz-brand-300)',
          400: 'var(--kz-brand-400)',
          500: 'var(--kz-brand-500)',
          600: 'var(--kz-brand-600)',
          700: 'var(--kz-brand-700)',
          800: 'var(--kz-brand-800)',
          900: 'var(--kz-brand-900)',
          950: 'var(--kz-brand-950)',
          soft:   'var(--kz-brand-soft)',
          hover:  'var(--kz-brand-hover)',
          strong: 'var(--kz-brand-strong)',
        },
        surface: {
          page:     'var(--kz-bg-page)',
          elevated: 'var(--kz-bg-elevated)',
          input:    'var(--kz-bg-input)',
          muted:    'var(--kz-bg-muted)',
          hover:    'var(--kz-bg-hover)',
        },
        ink: {
          primary:   'var(--kz-text-primary)',
          secondary: 'var(--kz-text-secondary)',
          muted:     'var(--kz-text-muted)',
          inverse:   'var(--kz-text-inverse)',
        },
        kz: {
          // Status soft fills (already covered by Tailwind defaults,
          // but exposed here as a semantic alias).
          'success-soft': 'var(--kz-success-50)',
          'success':      'var(--kz-success-600)',
          'success-dark': 'var(--kz-success-900)',
          'error-soft':   'var(--kz-error-50)',
          'error':        'var(--kz-error-600)',
          'error-dark':   'var(--kz-error-900)',
          'warning-soft': 'var(--kz-warning-50)',
          'warning':      'var(--kz-warning-600)',
          'warning-dark': 'var(--kz-warning-900)',
          'info-soft':    'var(--kz-info-50)',
          'info':         'var(--kz-info-600)',
          'info-dark':    'var(--kz-info-900)',
        },
      },
      fontFamily: {
        sans:   ['var(--kz-font-sans)', 'system-ui', 'sans-serif'],
        arabic: ['var(--kz-font-sans)', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card:    'var(--kz-radius-xl)',
        button:  'var(--kz-radius-lg)',
        chip:    'var(--kz-radius-sm)',
        modal:   'var(--kz-radius-2xl)',
      },
      borderWidth: {
        kz: 'var(--kz-border-width)', // 1.5px
      },
      boxShadow: {
        'kz-sm':      'var(--kz-shadow-sm)',
        'kz-md':      'var(--kz-shadow-md)',
        'kz-lg':      'var(--kz-shadow-lg)',
        'kz-xl':      'var(--kz-shadow-xl)',
        'kz-glow':    'var(--kz-shadow-glow)',
        'kz-brand':   'var(--kz-shadow-brand)',
        'kz-success': 'var(--kz-shadow-success)',
        'kz-error':   'var(--kz-shadow-error)',
        'kz-warning': 'var(--kz-shadow-warning)',
      },
      transitionDuration: {
        'kz-fast':   '80ms',
        'kz-normal': '220ms',
        'kz-slow':   '320ms',
      },
      transitionTimingFunction: {
        'kz':        'cubic-bezier(0.4, 0, 0.2, 1)',
        'kz-bounce': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
      },
    },
  },
  plugins: [],
};
