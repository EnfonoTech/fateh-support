// Site default currency — overridden at runtime by branding store if server advertises one.
let _defaultCurrency = "SAR";

export function setDefaultCurrency(code: string | null | undefined) {
  if (code && typeof code === "string") _defaultCurrency = code.toUpperCase();
}

export function getDefaultCurrency(): string {
  return _defaultCurrency;
}

function resolveCurrency(currency?: string | null): string {
  if (!currency) return _defaultCurrency;
  return currency.toUpperCase();
}

export interface FormatCurrencyOptions {
  digits?: number;
  /** Return HTML with the SAR symbol wrapped in <span class="sar-symbol"/>. */
  html?: boolean;
}

/**
 * Format a currency amount. For SAR we use the new Saudi Riyal glyph
 * (from the saudi_riyal web font); other currencies fall back to Intl.
 * Returns plain string by default; pass `html: true` to get the SAR
 * symbol wrapped in a styled span.
 */
export function formatCurrency(
  value: number | null | undefined,
  currency?: string | null,
  locale: string = "en",
  opts: FormatCurrencyOptions = {}
): string {
  const amount = typeof value === "number" && Number.isFinite(value) ? value : 0;
  const code = resolveCurrency(currency);
  const digits = opts.digits ?? 2;
  const numberText = formatNumber(amount, locale, digits);

  if (code === "SAR") {
    if (opts.html) return `<span class="sar-symbol" aria-label="SAR"></span>${numberText}`;
    // Text-only fallback (copy-paste friendly)
    return `SAR ${numberText}`;
  }

  try {
    return new Intl.NumberFormat(locale === "ar" ? "ar-SA" : "en-US", {
      style: "currency",
      currency: code,
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    }).format(amount);
  } catch {
    return `${code} ${numberText}`;
  }
}

/** Formatted money split into {symbol, amount} so templates can style the symbol freely. */
export function splitCurrency(
  value: number | null | undefined,
  currency?: string | null,
  locale: string = "en",
  digits: number = 2
): { code: string; amount: string; isSar: boolean } {
  const amount = typeof value === "number" && Number.isFinite(value) ? value : 0;
  const code = resolveCurrency(currency);
  return {
    code,
    amount: formatNumber(amount, locale, digits),
    isSar: code === "SAR",
  };
}

export function formatNumber(value: number, locale = "en", digits = 2): string {
  try {
    return new Intl.NumberFormat(locale === "ar" ? "ar-SA" : "en-US", {
      maximumFractionDigits: digits,
    }).format(value);
  } catch {
    return value.toFixed(digits);
  }
}

export function formatDateTime(value: string | Date | null | undefined, locale = "en"): string {
  if (!value) return "";
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.valueOf())) return "";
  return new Intl.DateTimeFormat(locale === "ar" ? "ar-SA" : "en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(d);
}

export function formatAge(seconds: number | null | undefined, locale = "en"): string {
  if (seconds == null || !Number.isFinite(seconds)) return "";
  if (seconds < 60) return locale === "ar" ? "الآن" : "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return locale === "ar" ? `${minutes} د` : `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return locale === "ar" ? `${hours} س` : `${hours}h`;
  const days = Math.floor(hours / 24);
  return locale === "ar" ? `${days} ي` : `${days}d`;
}
