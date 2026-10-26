"""The salary shown on a job card: only what the employer states, never an estimate.

Two places it can come from: the job platform's own salary field (freehire's engine passes it
on, see engine/main.go) or a pay range written in the ad. In the ad text a number only counts
when a pay word (salary, compensation, OTE...) is close to it, it has a currency, and it is
a plausible yearly amount: "€5K-€50K monthly TPV" or "$150M Series D" are not pay.
"""

import re

SYMBOLS = {"EUR": "€", "USD": "$", "GBP": "£", "€": "€", "$": "$", "£": "£"}
PAY_WORDS = re.compile(r"salar|compensation|\bpay\b|remuneration|retribuci|sueldo|\bOTE\b|\bbase\b", re.I)

CUR = r"(€|\$|£|EUR|USD|GBP)"
NUMBER = r"(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d\d)?|\d+(?:[.,]\d+)?)\s?([kK])?(?![\d.,]*\s?(?:[mMbB]\b|million|bn))"
AMOUNT = rf"{CUR}?\s?{NUMBER}\s?{CUR}?"
RANGE = re.compile(rf"{AMOUNT}\s*(?:-|–|—|to)\s*{AMOUNT}")
UP_TO = re.compile(rf"up to\s+{AMOUNT}", re.I)


def from_text(text):
    """A pay range stated in the ad, e.g. '€39.5k–54k', or '' when there is none."""
    for pattern in (RANGE, UP_TO):
        for match in pattern.finditer(text or ""):
            near = text[max(0, match.start() - 80):match.end() + 40]
            if not PAY_WORDS.search(near):
                continue
            # "R$", "C$", "A$" before, or a code like "MXN" after: another currency.
            if re.search(r"[A-Za-z]\Z", text[:match.start()]) and match.group(0)[0] in "$€£":
                continue
            if re.match(r"\s?(?!EUR|USD|GBP|OTE)[A-Z]{3}\b", text[match.end():]):
                continue
            parts = match.groups()
            currencies = [c for c in parts[0::4] + parts[3::4] if c]
            if not currencies:
                continue
            amounts = [_number(parts[i], parts[i + 1]) for i in range(1, len(parts), 4)]
            if not all(15000 <= a <= 1000000 for a in amounts) or amounts != sorted(amounts):
                continue
            low, high = (amounts + [None])[:2] if pattern is RANGE else (None, amounts[0])
            result = label(low, high, currencies[0].upper(), "year")
            after = text[match.end():match.end() + 25]
            return result + (" OTE" if re.search(r"\bOTE\b", after) else "")
    return ""


def label(low, high, currency, period):
    """Platform salary fields -> '€40k–55k', 'up to $70k', '€3k–4k/month' ('' if none)."""
    if not low and not high:
        return ""
    sign = SYMBOLS.get((currency or "").upper(), (currency or "") + " ")
    per = "" if period in ("", "year") else "/" + period
    if low and high and low != high:
        return f"{sign}{_short(low)}–{_short(high)}{per}"
    if high and not low:
        return f"up to {sign}{_short(high)}{per}"
    return f"{sign}{_short(low or high)}{per}"


def _number(digits, k):
    """'39.500' / '30,000' / '274,456.00' / '45' + 'k' -> 39500 / 30000 / 274456 / 45000."""
    digits = re.sub(r"(\d{3})[.,]\d\d$", r"\1", digits)  # drop cents
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", digits):
        value = float(re.sub(r"[.,]", "", digits))
    else:
        value = float(digits.replace(",", "."))
    return value * 1000 if k else value


def _short(value):
    """39500 -> '39.5k', 30000 -> '30k', 3000 -> '3k', 850 -> '850'."""
    if value < 1000:
        return f"{value:g}"
    return f"{value / 1000:.1f}".rstrip("0").rstrip(".") + "k"
