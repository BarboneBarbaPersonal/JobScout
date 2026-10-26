"""Salary shown on job cards: only what the ad states. Run: python -m unittest"""

import unittest

from scout import salary


class SalaryFromAd(unittest.TestCase):
    def test_ranges_stated_in_real_ads(self):
        cases = {
            "Spain €39.500 – €54.000 EUR *Pay Transparency at Mews*": "€39.5k–54k",
            "SaaS environments\n\nSpain\n€39.500 — €54.000 EUR\n*Pay Transparency at Mews*": "€39.5k–54k",
            "*Compensation:* A starting salary of €30,000 - €40,000 per year (depending on experience).": "€30k–40k",
            "*Transparent salary grids* from *34.000€ to 52.000€ OTE,* with a *70/30 split*": "€34k–52k OTE",
            "For Germany based hires: Estimated annual salary is between €123,000 - €169,000.": "€123k–169k",
            "*Compensation range (mix of salary and commission): $140,000-$170,000 USD.*": "$140k–170k",
            "Salary: 45k-55k EUR gross per year": "€45k–55k",
            "Base salary up to £60,000": "up to £60k",
            "Salary: $274,456.00 - $334,600.00/yr. This salary range represents": "$274.5k–334.6k",
            "base salary of $273,000.00 to $341,000.00 Equity": "$273k–341k",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(salary.from_text(text), expected)

    def test_money_that_is_not_pay(self):
        for text in [
            "a portfolio of small merchants transacting between €5K and €50K in monthly TPV",
            "€10 a day for lunch through our virtual canteen",
            "We've just reached unicorn status with a $150M Series D",
            "We've raised $781M in funding and our last valuation was $22B",
            "This role features a competitive base salary and a variable compensation structure",
            "Manage accounts worth €200,000 - €500,000 in annual revenue",
            "Pay Range $213,333.33 — $293,333.33 MXN Reasonable Accommodations",
            "Pay Range R$49,000 — R$70,000 BRL",
            "Salary range: C$90,000 - C$110,000",
        ]:
            with self.subTest(text=text):
                self.assertEqual(salary.from_text(text), "")


class SalaryFromPlatform(unittest.TestCase):
    def test_structured_fields(self):
        self.assertEqual(salary.label(40000, 55000, "EUR", "year"), "€40k–55k")
        self.assertEqual(salary.label(None, 70000, "USD", "year"), "up to $70k")
        self.assertEqual(salary.label(3000, 4000, "EUR", "month"), "€3k–4k/month")
        self.assertEqual(salary.label(None, None, "", ""), "")


if __name__ == "__main__":
    unittest.main()
